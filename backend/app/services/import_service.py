"""TripImportService — parse Excel/JSON trip files and import into DB."""

import io
import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip, TripSchedule


class TripImportService:
    """Parse and import trip files."""

    @staticmethod
    def generate_template_bytes() -> bytes:
        """Generate an Excel import template."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()

            # ── Sheet 1: 行程概要 ──
            ws1 = wb.active
            ws1.title = "行程概要"
            header_font = Font(bold=True, size=11, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            thin_border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'),
            )

            fields = [
                ("行程编号", "YN-2026-001", "唯一标识，如 YN-2026-001"),
                ("行程标题", "云南丽江古城5日深度游", "行程名称"),
                ("副标题", "遇见古城，邂逅纳西文化", "可选"),
                ("目的地", "云南丽江", "主要目的地"),
                ("详细目的地", "丽江古城,玉龙雪山,泸沽湖", "逗号分隔"),
                ("国家", "中国", "中国/日本/等"),
                ("省份", "云南", ""),
                ("城市", "丽江", ""),
                ("类型", "国内游", "国内游/出境游/周边游/定制游"),
                ("天数", "5", "整数"),
                ("晚数", "4", ""),
                ("出发城市", "北京", ""),
                ("最佳季节", "春季/秋季", ""),
                ("成人价", "3980", "元/人"),
                ("儿童价", "2680", "元/人"),
                ("婴儿价", "800", "元/人"),
                ("单房差", "800", "元"),
                ("费用包含", "往返机票,酒店,门票,导游", "逗号分隔"),
                ("费用不含", "个人消费,自费项目", "逗号分隔"),
                ("成团最小人数", "1", ""),
                ("成团最大人数", "30", ""),
                ("发团日期", "2026-07-15,2026-08-01", "逗号分隔的日期"),
            ]

            for i, (field, example, note) in enumerate(fields, 1):
                ws1.cell(row=i, column=1, value=field).font = Font(bold=True)
                ws1.cell(row=i, column=2, value=example)
                ws1.cell(row=i, column=3, value=note).font = Font(color="808080", italic=True)
                for col in range(1, 4):
                    ws1.cell(row=i, column=col).border = thin_border

            ws1.column_dimensions['A'].width = 18
            ws1.column_dimensions['B'].width = 35
            ws1.column_dimensions['C'].width = 30

            # ── Sheet 2: 行程安排 ──
            ws2 = wb.create_sheet("行程安排")
            schedule_headers = ["天数", "主题", "类型", "地点", "活动内容", "描述", "餐饮", "酒店名称", "酒店星级", "交通方式", "交通详情", "注意事项"]
            example_row = ["1", "出发抵达，初识丽江", "交通", "丽江三义机场", "接机入住酒店", "专车接机，入住四星级酒店，晚间自由逛古城", "晚餐", "丽江古城酒店", "4", "飞机+专车", "航班约3小时", "注意高原反应，多喝水"]

            for i, h in enumerate(schedule_headers, 1):
                cell = ws2.cell(row=1, column=i, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border
                ws2.column_dimensions[get_column_letter(i)].width = 14

            for i, val in enumerate(example_row, 1):
                ws2.cell(row=2, column=i, value=val).border = thin_border

            buf = io.BytesIO()
            wb.save(buf)
            return buf.getvalue()
        except ImportError:
            raise RuntimeError("openpyxl 未安装，无法生成模板")

    @staticmethod
    async def parse_and_import(
        content: bytes,
        filename: str,
        db: AsyncSession,
        created_by: str,
    ) -> dict:
        """Parse uploaded file and import into DB.

        Returns dict with: trip_id, trip_title, schedules_count, warnings
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        warnings = []

        if ext == "xlsx":
            parsed = TripImportService._parse_excel(content)
        elif ext == "json":
            parsed = json.loads(content.decode("utf-8"))
            parsed = {
                "trip": parsed.get("trip", parsed),
                "schedules": parsed.get("schedules", parsed.get("itinerary", [])),
            }
        else:
            raise ValueError(f"不支持的文件格式: .{ext}，请上传 .xlsx 或 .json")

        trip_data = parsed.get("trip", {})
        schedules_data = parsed.get("schedules", [])

        if not trip_data.get("title") and not trip_data.get("destination"):
            raise ValueError("无法解析行程信息：缺少标题或目的地")

        # Check duplicate code
        code = trip_data.get("code", "")
        if code:
            from sqlalchemy import select as sel
            existing = await db.execute(sel(Trip).where(Trip.code == code))
            if existing.scalar_one_or_none():
                code = f"{code}_imported"
                warnings.append(f"行程编号已存在，自动改为 {code}")

        if not code:
            import uuid as _uuid
            code = f"IMPORT-{_uuid.uuid4().hex[:8].upper()}"

        # Parse numeric fields
        def _int(v, default=0):
            try:
                return int(v) if v else default
            except (ValueError, TypeError):
                return default

        def _float(v, default=None):
            try:
                return float(v) if v else default
            except (ValueError, TypeError):
                return default

        def _list(v, default=None):
            if default is None:
                default = []
            if isinstance(v, list):
                return v
            if isinstance(v, str) and v.strip():
                return [x.strip() for x in v.split(",")]
            return default

        # Create trip
        trip = Trip(
            code=code,
            title=str(trip_data.get("title", "未命名行程")),
            subtitle=str(trip_data.get("subtitle", "")) if trip_data.get("subtitle") else None,
            destination=str(trip_data.get("destination", "")),
            destinations_detail=_list(trip_data.get("destinations_detail", trip_data.get("详细目的地"))),
            country=str(trip_data.get("country", "中国")),
            province=str(trip_data.get("province", "")) if trip_data.get("province") else None,
            city=str(trip_data.get("city", "")) if trip_data.get("city") else None,
            category=str(trip_data.get("category", trip_data.get("类型", "国内游"))),
            duration_days=_int(trip_data.get("duration_days", trip_data.get("天数"), 1)),
            duration_nights=_int(trip_data.get("duration_nights", trip_data.get("晚数"))),
            departure_city=str(trip_data.get("departure_city", trip_data.get("出发城市", ""))) if trip_data.get("departure_city") else None,
            best_season=str(trip_data.get("best_season", trip_data.get("最佳季节", ""))) if trip_data.get("best_season") else None,
            price_adult=_float(trip_data.get("price_adult", trip_data.get("成人价"))),
            price_child=_float(trip_data.get("price_child", trip_data.get("儿童价"))),
            price_infant=_float(trip_data.get("price_infant", trip_data.get("婴儿价"))),
            single_room_supplement=_float(trip_data.get("single_room_supplement", trip_data.get("单房差"))),
            price_includes=_list(trip_data.get("price_includes", trip_data.get("费用包含"))),
            price_excludes=_list(trip_data.get("price_excludes", trip_data.get("费用不含"))),
            group_size_min=_int(trip_data.get("group_size_min", trip_data.get("成团最小人数"), 1)),
            group_size_max=_int(trip_data.get("group_size_max", trip_data.get("成团最大人数"))) or None,
            departure_dates=_list(trip_data.get("departure_dates", trip_data.get("发团日期"))),
            status="active",
            created_by=created_by,
        )
        db.add(trip)
        await db.flush()

        # Create schedules
        schedule_count = 0
        for s in schedules_data:
            day = _int(s.get("day_number", s.get("天数", s.get("day", 0))))
            if day <= 0:
                continue
            schedule = TripSchedule(
                trip_id=trip.id,
                day_number=day,
                theme=str(s.get("theme", s.get("主题", ""))) if s.get("theme") or s.get("主题") else None,
                schedule_type=str(s.get("schedule_type", s.get("类型", "景点"))),
                location=str(s.get("location", s.get("地点", ""))) if s.get("location") or s.get("地点") else None,
                activity=str(s.get("activity", s.get("活动内容", ""))) if s.get("activity") or s.get("活动内容") else None,
                description=str(s.get("description", s.get("描述", ""))) if s.get("description") or s.get("描述") else None,
                meal_included=str(s.get("meal_included", s.get("餐饮", ""))) if s.get("meal_included") or s.get("餐饮") else None,
                hotel_name=str(s.get("hotel_name", s.get("酒店名称", ""))) if s.get("hotel_name") or s.get("酒店名称") else None,
                hotel_stars=_int(s.get("hotel_stars", s.get("酒店星级"))) or None,
                transport_type=str(s.get("transport_type", s.get("交通方式", ""))) if s.get("transport_type") or s.get("交通方式") else None,
                transport_detail=str(s.get("transport_detail", s.get("交通详情", ""))) if s.get("transport_detail") or s.get("交通详情") else None,
                tips=str(s.get("tips", s.get("注意事项", ""))) if s.get("tips") or s.get("注意事项") else None,
                sort_order=schedule_count,
            )
            db.add(schedule)
            schedule_count += 1

        await db.flush()

        return {
            "trip_id": str(trip.id),
            "trip_title": trip.title,
            "schedules_count": schedule_count,
            "validation_warnings": warnings,
        }

    @staticmethod
    def _parse_excel(content: bytes) -> dict:
        """Parse Excel file into trip + schedules dict."""
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)

        trip_data = {}
        schedules = []

        # Parse overview sheet
        for sheet_name in ["行程概要", "概览", "Sheet1"]:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                for row in ws.iter_rows(min_row=1, values_only=True):
                    if row[0] and row[1]:
                        key = str(row[0]).strip()
                        val = row[1]
                        if key and val:
                            field_map = {
                                "行程编号": "code", "行程标题": "title", "副标题": "subtitle",
                                "目的地": "destination", "详细目的地": "destinations_detail",
                                "国家": "country", "省份": "province", "城市": "city",
                                "类型": "category", "天数": "duration_days", "晚数": "duration_nights",
                                "出发城市": "departure_city", "最佳季节": "best_season",
                                "成人价": "price_adult", "儿童价": "price_child", "婴儿价": "price_infant",
                                "单房差": "single_room_supplement",
                                "费用包含": "price_includes", "费用不含": "price_excludes",
                                "成团最小人数": "group_size_min", "成团最大人数": "group_size_max",
                                "发团日期": "departure_dates",
                            }
                            field = field_map.get(key, key)
                            trip_data[field] = val
                break

        # Parse schedule sheet
        for sheet_name in ["行程安排", "日程", "行程表"]:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = list(ws.iter_rows(min_row=1, values_only=True))
                if not rows:
                    continue
                headers = [str(h).strip() if h else "" for h in rows[0]]
                header_map = {
                    "天数": "day_number", "天": "day_number", "day": "day_number",
                    "主题": "theme", "类型": "schedule_type", "type": "schedule_type",
                    "地点": "location", "活动内容": "activity", "活动": "activity",
                    "描述": "description", "内容": "description",
                    "餐饮": "meal_included", "餐": "meal_included",
                    "酒店名称": "hotel_name", "酒店": "hotel_name", "住宿": "hotel_name",
                    "酒店星级": "hotel_stars", "星级": "hotel_stars",
                    "交通方式": "transport_type", "交通": "transport_type",
                    "交通详情": "transport_detail",
                    "注意事项": "tips", "注意": "tips",
                }
                for row in rows[1:]:
                    if not any(row):
                        continue
                    schedule = {}
                    for i, cell in enumerate(row):
                        if i >= len(headers) or cell is None:
                            continue
                        h = headers[i].lower() if headers[i] else ""
                        field = header_map.get(headers[i], header_map.get(h, h))
                        schedule[field] = str(cell).strip() if cell else ""
                    if schedule.get("day_number"):
                        try:
                            schedule["day_number"] = int(str(schedule["day_number"]).replace("第", "").replace("天", ""))
                        except ValueError:
                            schedule["day_number"] = len(schedules) + 1
                    else:
                        schedule["day_number"] = len(schedules) + 1
                    schedules.append(schedule)
                break

        return {"trip": trip_data, "schedules": schedules}
