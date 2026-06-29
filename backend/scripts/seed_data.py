"""
Seed the database with sample trip data.
Run:   python -m scripts.seed_data
Works with both SQLite (local dev) and PostgreSQL.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.base import async_session_factory, Base, engine, is_sqlite
from app.models.customer import Customer, CustomerProfile
from app.models.trip import Trip, TripSchedule
from app.utils.auth import get_password_hash

# Import all models to register with Base
from app.models.order import Order  # noqa: F401
from app.models.video_script import VideoScript  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.document_chunk import DocumentChunk  # noqa: F401
from app.models.feedback import Feedback  # noqa: F401

SAMPLE_TRIPS = [
    {
        "code": "YN-LJ-2026-001",
        "title": "云南丽江古城5日深度游",
        "subtitle": "遇见古城，邂逅纳西文化",
        "destination": "云南丽江",
        "destinations_detail": ["丽江古城", "玉龙雪山", "束河古镇", "泸沽湖", "拉市海"],
        "country": "中国", "province": "云南", "city": "丽江",
        "category": "国内游", "duration_days": 5, "duration_nights": 4,
        "departure_city": "北京", "best_season": "春季/秋季",
        "price_adult": 3980, "price_child": 2680, "price_infant": 800,
        "price_includes": ["往返机票", "4晚酒店住宿", "全程大巴", "行程所列门票", "导游服务", "旅游保险"],
        "price_excludes": ["个人消费", "单房差800元", "自费项目"],
        "summary": "经典云南丽江深度游线路，涵盖丽江古城、玉龙雪山、束河古镇、泸沽湖等精华景点。全程入住四星级酒店，品尝地道纳西美食，体验茶马古道文化。适合家庭出游、摄影爱好者和文化探索者。",
        "highlights": [
            "登玉龙雪山冰川公园，海拔4506米观景台",
            "夜游丽江古城，体验纳西族篝火晚会",
            "泸沽湖猪槽船游湖，探访摩梭人家",
            "茶马古道骑马体验，穿越原始森林",
        ],
        "recommendation_reasons": [
            "云南必去的经典线路，适合首次云南游的客人",
            "性价比高，全程含机票酒店门票",
            "四季皆宜，春有花海、秋有彩林",
        ],
        "departure_dates": ["2026-07-15", "2026-08-01", "2026-08-20", "2026-09-10"],
        "schedules": [
            {"day": 1, "theme": "出发抵达，初识丽江", "type": "交通/住宿", "desc": "乘航班抵达丽江三义机场，专车接机入住酒店，晚间自由逛古城"},
            {"day": 2, "theme": "玉龙雪山一日游", "type": "景点", "desc": "乘索道登玉龙雪山冰川公园，下午游览蓝月谷，晚上观看《印象丽江》演出"},
            {"day": 3, "theme": "泸沽湖探秘", "type": "景点/交通", "desc": "驱车前往泸沽湖(4小时)，猪槽船游湖，参观走婚桥，入住湖景客栈"},
            {"day": 4, "theme": "摩梭文化体验", "type": "文化/景点", "desc": "上午参观摩梭博物馆，下午返回丽江，途径宁蒗彝族村寨"},
            {"day": 5, "theme": "束河古镇，返程", "type": "景点/交通", "desc": "上午游览束河古镇和拉市海，下午送机返程"},
        ],
    },
    {
        "code": "HN-SY-2026-002",
        "title": "海南三亚5天4晚阳光海岛度假",
        "subtitle": "碧海蓝天，热带天堂",
        "destination": "海南三亚",
        "destinations_detail": ["亚龙湾", "蜈支洲岛", "天涯海角", "南山文化苑", "三亚免税城"],
        "country": "中国", "province": "海南", "city": "三亚",
        "category": "国内游", "duration_days": 5, "duration_nights": 4,
        "departure_city": "上海", "best_season": "冬季/春季",
        "price_adult": 5280, "price_child": 3580, "price_infant": 1000,
        "price_includes": ["往返机票", "4晚五星海景酒店", "行程所列门票", "当地用车", "导游服务"],
        "price_excludes": ["个人消费", "单房差1500元", "水上项目自费"],
        "summary": "三亚经典海岛度假线路，入住五星海景酒店，畅游亚龙湾白沙滩，登蜈支洲岛体验潜水，朝圣南山海上观音，尽享热带海岛风情。亲子友好，适合全家出行。",
        "highlights": [
            "亚龙湾私人沙滩，尽享碧海蓝天",
            "蜈支洲岛潜水体验，探索珊瑚礁世界",
            "108米南山海上观音，祈福平安",
            "三亚国际免税城自由购物",
        ],
        "recommendation_reasons": [
            "冬季最佳避寒胜地，适合全家老小",
            "五星海景酒店，推窗见海",
            "亲子友好，包含儿童俱乐部活动",
        ],
        "departure_dates": ["2026-07-20", "2026-08-05", "2026-08-15"],
        "schedules": [
            {"day": 1, "theme": "飞抵三亚，入住海景酒店", "type": "交通/住宿", "desc": "抵达三亚凤凰机场，专车接机，入住亚龙湾五星海景酒店"},
            {"day": 2, "theme": "蜈支洲岛一日游", "type": "景点/水上活动", "desc": "乘船前往蜈支洲岛，体验潜水或浮潜，沙滩漫步，午餐岛上自助"},
            {"day": 3, "theme": "南山文化之旅", "type": "文化/景点", "desc": "参观南山文化苑，朝拜108米海上观音，品尝素斋，下午天涯海角"},
            {"day": 4, "theme": "自由活动+免税购物", "type": "自由活动/购物", "desc": "上午自由享受酒店设施或沙滩，下午前往三亚国际免税城"},
            {"day": 5, "theme": "告别三亚", "type": "交通", "desc": "上午自由活动，下午专车送机，告别阳光海岛"},
        ],
    },
    {
        "code": "RB-DJ-2026-003",
        "title": "日本东京京都大阪7日经典游",
        "subtitle": "和风文化，从古都到现代",
        "destination": "日本（东京-京都-大阪）",
        "destinations_detail": ["东京", "富士山", "京都", "奈良", "大阪"],
        "country": "日本", "province": None, "city": "东京",
        "category": "出境游", "duration_days": 7, "duration_nights": 6,
        "departure_city": "北京", "best_season": "春季/秋季",
        "price_adult": 12800, "price_child": 9800, "price_infant": 3000,
        "price_includes": ["往返机票", "6晚酒店", "JR Pass 7日券", "行程所列门票", "导游+领队", "签证费"],
        "price_excludes": ["个人消费", "单房差3000元", "自费餐饮"],
        "summary": "经典日本本州7日游，从东京的繁华到京都的古韵，横跨关东关西。登富士山五合目，穿和服漫步京都古街，奈良公园喂小鹿，大阪心斋桥购物。全程中文领队，适合首次出境游。",
        "highlights": [
            "富士山五合目观景，箱根温泉体验",
            "京都金阁寺+伏见稻荷大社千本鸟居",
            "奈良公园与鹿共舞，东大寺世界遗产",
            "东京浅草寺、银座、秋叶原自由探索",
        ],
        "recommendation_reasons": [
            "日本最经典线路，涵盖关东+关西精华",
            "春秋两季最佳，樱花季和红叶季一票难求",
            "全程中文领队，适合首次出境游",
        ],
        "departure_dates": ["2026-09-15", "2026-10-10", "2026-11-01"],
        "schedules": [
            {"day": 1, "theme": "飞抵东京", "type": "交通/住宿", "desc": "北京飞东京成田，专车接机，入住新宿酒店"},
            {"day": 2, "theme": "东京经典一日", "type": "景点/文化", "desc": "浅草寺→天空树→秋叶原→银座，晚上可自费东京塔夜景"},
            {"day": 3, "theme": "富士山+箱根", "type": "景点/温泉", "desc": "乘车上富士山五合目，芦之湖海盗船，箱根温泉酒店入住"},
            {"day": 4, "theme": "新干线→京都", "type": "交通/景点", "desc": "乘新干线前往京都，下午金阁寺+龙安寺，晚上祇园散步"},
            {"day": 5, "theme": "京都古韵一日", "type": "文化/景点", "desc": "伏见稻荷大社千本鸟居→清水寺→二年坂三年坂，和服体验"},
            {"day": 6, "theme": "奈良+大阪", "type": "景点/购物", "desc": "奈良公园喂鹿、东大寺，下午前往大阪道顿堀+心斋桥购物"},
            {"day": 7, "theme": "返程", "type": "交通", "desc": "上午自由活动，下午关西机场送机，结束愉快的日本之旅"},
        ],
    },
]


async def seed():
    """Seed sample data."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        from sqlalchemy import select, func

        # Check if data exists
        count_result = await db.execute(select(func.count()).select_from(Trip))
        if count_result.scalar() > 0:
            print("数据库已有数据，跳过种子填充。")
            return

        db_type = 'SQLite' if is_sqlite() else 'PostgreSQL'
        print(f"Database: {db_type}")
        print("Seeding test data...")

        # Create shop owner
        shop_owner = Customer(
            phone="13800000001", name="张店长", role="shop_owner",
            email="admin@huanyou.com",
        )
        shop_owner.password_hash = get_password_hash("admin123")
        db.add(shop_owner)

        # Create test user
        test_user = Customer(
            phone="13800000002", name="李游客", role="user",
            email="user@test.com",
        )
        test_user.password_hash = get_password_hash("user123")
        db.add(test_user)
        await db.flush()

        # User profile
        profile = CustomerProfile(
            customer_id=test_user.id,
            age_group="青年", city="北京",
            preferred_destinations=["云南", "海南", "日本"],
            preferred_categories=["自然风光", "海岛度假"],
            budget_range_min=3000, budget_range_max=15000,
            preferred_duration_days=5, preferred_season="春季",
            travel_style="跟团游", booking_frequency="中频",
            interest_tags=["摄影", "美食", "徒步"],
            profile_summary="青年用户，偏好云南和海南等自然风光目的地，消费区间3000-15000元，通常选择5天左右的跟团游。",
        )
        db.add(profile)
        await db.flush()

        # Create trips
        for trip_data in SAMPLE_TRIPS:
            schedules_data = trip_data.pop("schedules")
            trip = Trip(
                created_by=shop_owner.id, status="active",
                is_featured=(trip_data["code"] == "YN-LJ-2026-001"),
                **trip_data,
            )
            db.add(trip)
            await db.flush()

            for i, s in enumerate(schedules_data):
                schedule = TripSchedule(
                    trip_id=trip.id,
                    day_number=s["day"], theme=s["theme"],
                    schedule_type=s["type"], description=s["desc"],
                    sort_order=i,
                )
                db.add(schedule)
            await db.flush()
            print(f"  [OK] {trip.code} - {trip.title}")

        await db.commit()
        print(f"\n[OK] 种子数据填充完成!")
        print(f"   店长: 13800000001 / admin123")
        print(f"   用户: 13800000002 / user123")
        print(f"   行程: {len(SAMPLE_TRIPS)} 条")


if __name__ == "__main__":
    asyncio.run(seed())
