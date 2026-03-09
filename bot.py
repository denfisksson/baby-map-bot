import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import config
from services.geocoding import GeocodingService
from services.location_search import LocationSearchService

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize services
geocoding_service = GeocodingService()
location_service = LocationSearchService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to Baby-Friendly Spots Bot!\n\n"
        "I help you find baby-friendly locations like cafes, parks, playgrounds, "
        "and more for babies.\n\n"
        "📍 Just send me a location name (e.g., 'Prague', 'Old Town Square, Prague', 'St. Vitus Cathedral') "
        "and I'll show you nearby baby-friendly spots!\n\n"
        "Use /help to see all available commands."
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help information when the command /help is issued."""
    help_message = (
        "🤖 *How to use this bot:*\n\n"
        "Simply send me a location name, and I'll help you find baby-friendly spots!\n\n"
        "*How it works:*\n"
        "1. Send me a location (e.g., 'Prague', 'Old Town Square')\n"
        "2. Choose what you're looking for (cafes, parks, museums, etc.)\n"
        "3. Browse the results!\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
    )
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages (location queries)."""
    user_message = update.message.text
    logger.info(f"Received message from {update.effective_user.id}: {user_message}")

    # Send "searching" message
    searching_msg = await update.message.reply_text(
        f"🔍 Looking up '{user_message}'..."
    )

    # Step 1: Geocode the location
    location_data = geocoding_service.geocode(user_message)
    if not location_data:
        await searching_msg.edit_text(
            f"❌ Sorry, I couldn't find the location '{user_message}'.\n\n"
            "Please try:\n"
            "• Being more specific (e.g., 'Prague, Czech Republic')\n"
            "• Using a different name\n"
            "• Checking for typos"
        )
        return

    # Step 2: Store location data for category selection
    context.user_data['location_data'] = location_data
    context.user_data['location_query'] = user_message

    # Step 3: Show category selection buttons
    keyboard = [
        [
            InlineKeyboardButton("☕ Cafes & Restaurants", callback_data="cat:cafes"),
            InlineKeyboardButton("🌳 Parks & Playgrounds", callback_data="cat:parks"),
        ],
        [
            InlineKeyboardButton("🏛️ Museums", callback_data="cat:museums"),
            InlineKeyboardButton("🎢 Indoor Activities", callback_data="cat:indoor"),
        ],
        [
            InlineKeyboardButton("🔍 Show All", callback_data="cat:all"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await searching_msg.edit_text(
        f"📍 Found: {location_data['display_name']}\n\n"
        "What type of baby-friendly spots are you looking for?",
        reply_markup=reply_markup
    )


def _get_venue_emoji(venue_type: str) -> str:
    """Get emoji for venue type."""
    emoji_map = {
        'Playground': '🎠',
        'Park': '🌳',
        'Cafe': '☕',
        'Restaurant': '🍽️',
        'Fast Food': '🍔',
        'Museum': '🏛️',
        'Zoo': '🦁',
        'Theme Park': '🎢',
        'Water Park': '🏊',
    }
    return emoji_map.get(venue_type, '📍')


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category button clicks."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    # Extract category from callback_data (format: "cat:cafes")
    category = query.data.split(':')[1]

    # Retrieve stored location data
    location_data = context.user_data.get('location_data')
    location_query = context.user_data.get('location_query')

    if not location_data:
        await query.edit_message_text("❌ Session expired. Please search again.")
        return

    # Update message to show searching
    category_display = category.replace('_', ' ').title()
    if category == 'all':
        category_display = 'all baby-friendly spots'

    await query.edit_message_text(
        f"🔍 Searching for {category_display} near {location_query}..."
    )

    # Search venues with category filter
    venues = location_service.search_nearby_venues(
        lat=location_data['lat'],
        lon=location_data['lon'],
        radius_km=config.DEFAULT_SEARCH_RADIUS_KM,
        max_results=config.MAX_RESULTS,
        category=category
    )

    if not venues:
        await query.edit_message_text(
            f"😔 No {category_display} found near {location_data['display_name']}.\n\n"
            "Try searching for a different location or category."
        )
        return

    # Format and send results
    response = f"📍 *{category_display.title()} near {location_query}*\n"
    response += f"_{location_data['display_name']}_\n\n"

    for i, venue in enumerate(venues, 1):
        emoji = _get_venue_emoji(venue['type'])
        response += f"{i}. {emoji} *{venue['name']}*\n"
        response += f"   Type: {venue['type']}\n"
        response += f"   Distance: {venue['distance_km']} km\n"

        if venue['address'] != 'Address not available':
            response += f"   📍 {venue['address']}\n"

        map_url = f"https://www.google.com/maps?q={venue['lat']},{venue['lon']}"
        response += f"   [View on map]({map_url})\n\n"

    await query.edit_message_text(
        response,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Register callback handler for category selection
    application.add_handler(CallbackQueryHandler(category_callback, pattern="^cat:"))

    # Register message handler for location queries
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
