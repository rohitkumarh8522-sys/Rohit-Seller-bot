import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 1234567890))

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"

BOT_CONFIG = {
    "product_name": "Premium Digital Pass",
    "product_price": "₹199",
    "qr_code_url": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa=rohit0853@ptaxis%26pn=Rohit",
    "upi_id": "rohit0853@ptaxis",
    "product_link": "https://t.me/+YourSecretGroupLinkHere",
    "support_username": "@G_KlNG"
}
# =======================================================

app = Client("BusinessBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_states = {}

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    text = (
        f"👋 Welcome to **{BOT_CONFIG['product_name']}** Bot!\n\n"
        f"📌 **Price:** {BOT_CONFIG['product_price']}\n"
        f"💬 **Support:** {BOT_CONFIG['support_username']}\n\n"
        "Neeche diye gaye **Buy Now** button par click karke payment karein."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Now", callback_data="buy_now")],
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{BOT_CONFIG['support_username'].replace('@', '')}")]
    ])
    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("^buy_now$"))
async def buy_now_handler(client: Client, callback: CallbackQuery):
    user_states[callback.from_user.id] = "WAITING_SCREENSHOT"
    
    caption = (
        f"💳 **Payment details for {BOT_CONFIG['product_name']}**\n\n"
        f"💰 Amount: **{BOT_CONFIG['product_price']}**\n"
        f"📍 UPI ID: `{BOT_CONFIG['upi_id']}`\n\n"
        "1. QR Scan karke payment karein.\n"
        "2. Payment complete hone ke baad **Screenshot yahan send karein**."
    )
    
    await callback.message.reply_photo(
        photo=BOT_CONFIG["qr_code_url"],
        caption=caption
    )
    await callback.answer()

@app.on_message(filters.photo & filters.private)
async def screenshot_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if user_states.get(user_id) == "WAITING_SCREENSHOT":
        user_states[user_id] = None 
        
        admin_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
            ]
        ])
        
        await client.send_photo(
            chat_id=ADMIN_ID,
            photo=message.photo.file_id,
            caption=(
                f"📥 **New Payment Request Received!**\n\n"
                f"👤 **User:** {message.from_user.first_name} (@{message.from_user.username})\n"
                f"🆔 **User ID:** `{user_id}`"
            ),
            reply_markup=admin_keyboard
        )
        
        await message.reply_text("✅ Payment screenshot received! Verification chal rahi hai, jaldi hi aapko link mil jayega.")
    else:
        await message.reply_text("Pehle /start dabayein aur Buy Now select karein.")

@app.on_callback_query(filters.regex("^approve_"))
async def approve_payment(client: Client, callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Unauthorized", show_alert=True)
        
    target_user_id = int(callback.data.split("_")[1])
    
    try:
        await client.send_message(
            chat_id=target_user_id,
            text=(
                f"🎉 **Payment Verified Successfully!**\n\n"
                f"Aapka link ready hai:\n🔗 {BOT_CONFIG['product_link']}"
            )
        )
        await callback.edit_message_caption(
            caption=callback.message.caption + "\n\n✅ **Approved by Admin**"
        )
    except Exception as e:
        await callback.answer(f"Failed to send link: {e}", show_alert=True)

@app.on_callback_query(filters.regex("^reject_"))
async def reject_payment(client: Client, callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Unauthorized", show_alert=True)
        
    target_user_id = int(callback.data.split("_")[1])
    
    try:
        await client.send_message(
            chat_id=target_user_id,
            text="❌ **Payment Verification Failed.** Kripya correct screenshot bhejein ya Support par baat karein."
        )
        await callback.edit_message_caption(
            caption=callback.message.caption + "\n\n❌ **Rejected by Admin**"
        )
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)

@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    text = (
        "⚙️ **Admin Panel**\n\n"
        f"• **Product:** {BOT_CONFIG['product_name']}\n"
        f"• **Price:** {BOT_CONFIG['product_price']}\n"
        f"• **UPI ID:** {BOT_CONFIG['upi_id']}\n"
        f"• **Link:** {BOT_CONFIG['product_link']}\n\n"
        "ℹ️ *Note: Configuration code ke andar hardcoded hai.*"
    )
    await message.reply_text(text)

async def web_server():
    routes = web.RouteTableDef()
    @routes.get("/")
    async def index(request):
        return web.Response(text="Bot is Live and Running!")
    
    app_web = web.Application()
    app_web.add_routes(routes)
    return app_web

