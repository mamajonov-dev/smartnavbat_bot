import db
async def barber_statistics(barber_id, date):
    async with db.pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE status='confirmed') AS confirmed_count,
                COUNT(*) FILTER (WHERE status='canceled') AS canceled_count,
                COUNT(*) FILTER (WHERE status='pending') AS pending_count
            FROM bookings
            WHERE barber_id=$1 AND DATE(slot_time)=$2
        """, barber_id, date)
        return stats


async def user_statistics(user_id):
    async with db.pool.acquire() as conn:
        # stats = await conn.fetchrow("""
        #     SELECT
        #         COUNT(*) FILTER (WHERE status='confirmed') AS confirmed_count,
        #         COUNT(*) FILTER (WHERE status='canceled') AS canceled_count,
        #         no_show_count,
        #         blocked
        #     FROM users
        #     WHERE id=$1
        # """, user_id)
        # return stats
        # Booking statistikasi
        booking_stats = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE status='confirmed') AS confirmed_count,
                COUNT(*) FILTER (WHERE status='canceled') AS canceled_count,
                COUNT(*) FILTER (WHERE status='pending') AS pending_count
            FROM bookings
            WHERE user_id=$1
        """, user_id)

        # User info
        user_info = await conn.fetchrow("""
            SELECT no_show_count, blocked
            FROM users
            WHERE id=$1
        """, user_id)
        return booking_stats


