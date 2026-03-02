import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
        "Simply send me a location name, and I'll find baby-friendly spots nearby!\n\n"
        "*Commands:*\n"
        "/start - Start the bot and see welcome message\n"
        "/help - Show this help message\n\n"
        "*Examples:*\n"
        "• Prague\n"
        "• Old Town Square, Prague\n"
        "• St. Vitus Cathedral\n\n"
        "📍 You can also share your GPS location for more accurate results (coming soon)!"
    )
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages (location queries)."""
    user_message = update.message.text
    logger.info(f"Received message from {update.effective_user.id}: {user_message}")

    # Send "searching" message
    searching_msg = await update.message.reply_text(
        f"🔍 Searching for baby-friendly spots near '{user_message}'..."
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

    # Step 2: Search for nearby venues
    venues = location_service.search_nearby_venues(
        lat=location_data['lat'],
        lon=location_data['lon'],
        radius_km=config.DEFAULT_SEARCH_RADIUS_KM,
        max_results=config.MAX_RESULTS
    )

    if not venues:
        await searching_msg.edit_text(
            f"😔 No baby-friendly spots found near {location_data['display_name']}.\n\n"
            "Try searching for a different location or a larger city nearby."
        )
        return

    # Step 3: Format and send results
    response = f"📍 *Baby-friendly spots near {user_message}*\n"
    response += f"_{location_data['display_name']}_\n\n"

    for i, venue in enumerate(venues, 1):
        emoji = _get_venue_emoji(venue['type'])
        response += f"{i}. {emoji} *{venue['name']}*\n"
        response += f"   Type: {venue['type']}\n"
        response += f"   Distance: {venue['distance_km']} km\n"

        if venue['address'] != 'Address not available':
            response += f"   📍 {venue['address']}\n"

        # Add map link
        map_url = f"https://www.google.com/maps?q={venue['lat']},{venue['lon']}"
        response += f"   [View on map]({map_url})\n\n"

    await searching_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)


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

    # Register message handler for location queries
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
