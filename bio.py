import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import data_pb2

BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_ID = int(os.getenv('ADMIN_ID', 'YOUR_ADMIN_ID_HERE'))

ACCESS_TOKEN_URL = "https://access-token-narayan.vercel.app/token?access={}&key=Narayan"
BIO_UPDATE_URL = "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
FREEFIRE_VERSION = "OB50"

async def set_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setbio <access_token> <new_bio_text>")
        return

    access_token = context.args[0]
    bio_text = ' '.join(context.args[1:])

    token_resp = requests.get(ACCESS_TOKEN_URL.format(access_token))
    if token_resp.status_code != 200:
        await update.message.reply_text("❌ Failed to fetch JWT token.")
        return

    token_json = token_resp.json()
    jwt_token = token_json.get("token")

    if not jwt_token:
        await update.message.reply_text("❌ Token not found in response.")
        return

    data = data_pb2.Data()
    data.field_2 = 17
    data.field_5.CopyFrom(data_pb2.EmptyMessage())
    data.field_6.CopyFrom(data_pb2.EmptyMessage())
    data.field_8 = bio_text
    data.field_9 = 1
    data.field_11.CopyFrom(data_pb2.EmptyMessage())
    data.field_12.CopyFrom(data_pb2.EmptyMessage())

    data_bytes = data.SerializeToString()
    padded_data = pad(data_bytes, AES.block_size)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    encrypted_data = cipher.encrypt(padded_data)
    data_bytes = bytes.fromhex(''.join(f"{b:02X}" for b in encrypted_data))

    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {jwt_token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": FREEFIRE_VERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    res = requests.post(BIO_UPDATE_URL, headers=headers, data=data_bytes)

    if res.status_code == 200:
        await update.message.reply_text(f"✅ Bio updated successfully:\n\n{bio_text}")
    else:
        await update.message.reply_text(f"❌ Failed to update bio. Status code: {res.status_code}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('setbio', set_bio))
    print("✅ Bot is running...")
    app.run_polling()