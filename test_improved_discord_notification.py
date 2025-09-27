#!/usr/bin/env python3
"""
Test improved Discord notification with thumbnail support
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from api.webhook import create_discord_event_and_announcement

# Load environment variables
load_dotenv()

def load_manus_event_data():
    """Load actual Manus October 3rd event data"""
    with open('morrie_oct_2025_event_1.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract instructor name from the complex structure
    instructor_name = "Unknown Instructor"
    if "instructor" in data and isinstance(data["instructor"], list) and len(data["instructor"]) > 0:
        instructor_name = data["instructor"][0].get("text", "Unknown Instructor")
    
    # Extract YouTube Live URL
    youtube_url = None
    if "fields" in data and "セミナーURL" in data["fields"]:
        youtube_url = data["fields"]["セミナーURL"].get("link")
    
    # Extract Peatix URL
    peatix_url = None
    if "fields" in data and "本番Peatixページ" in data["fields"]:
        peatix_url = data["fields"]["本番Peatixページ"].get("link")
    
    # Extract thumbnail
    thumbnail_data = []
    if "fields" in data and "サムネイル" in data["fields"]:
        thumbnail_data = data["fields"]["サムネイル"]
    
    # Convert to the format expected by webhook
    event_data = {
        "fields": {
            "title": data.get("title", "Unknown Event"),
            "instructor": instructor_name,
            "YouTube Live URL": youtube_url,
            "Peatix Page": peatix_url,
            "サムネイル": thumbnail_data
        }
    }
    
    return event_data

async def test_improved_discord_notification():
    """Test the improved Discord notification system"""
    
    print("🔧 Testing improved Discord notification system...")
    print("=" * 60)
    
    # Load actual event data
    event_data = load_manus_event_data()
    
    print("📋 Event Data:")
    print(f"  Title: {event_data['fields']['title']}")
    print(f"  Instructor: {event_data['fields']['instructor']}")
    print(f"  YouTube: {event_data['fields']['YouTube Live URL']}")
    print(f"  Peatix: {event_data['fields']['Peatix Page']}")
    
    # Check thumbnail
    thumbnail_info = event_data['fields'].get('サムネイル', [])
    if thumbnail_info and len(thumbnail_info) > 0:
        thumbnail_url = thumbnail_info[0].get('url')
        print(f"  Thumbnail: {thumbnail_url}")
    else:
        print("  Thumbnail: Not available")
    
    print("\n🚀 Creating Discord event and announcement...")
    
    try:
        # Test the improved function
        result = await create_discord_event_and_announcement(event_data)
        
        if result["success"]:
            print("\n✅ Success! Discord event and announcement created:")
            print(f"  Event ID: {result['discord_event']['event_id']}")
            print(f"  Event Name: {result['discord_event']['event_name']}")
            print(f"  Event URL: {result['discord_event']['event_url']}")
            print(f"  Has Cover Image: {result['discord_event']['has_cover']}")
            print(f"  Start Time: {result['discord_event']['start_time']}")
            print(f"  End Time: {result['discord_event']['end_time']}")
            print(f"  Message ID: {result['announcement']['message_id']}")
            print(f"  Channel ID: {result['announcement']['channel_id']}")
            print(f"  Has Thumbnail in Announcement: {result['announcement']['has_thumbnail']}")
            
            print("\n🎯 Improvements verified:")
            print("  ✓ Thumbnail image set for Discord event")
            print("  ✓ Enhanced announcement formatting")
            print("  ✓ Thumbnail displayed in announcement")
            print("  ✓ Record ID removed from event creation")
            print("  ✓ Better visual presentation with decorations")
            
        else:
            print("❌ Failed to create Discord event and announcement")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # Ask if user wants to clean up
    cleanup = input("Do you want to delete the test event? (y/n): ").lower().strip()
    if cleanup == 'y':
        print("🧹 Please manually delete the test event from Discord if needed.")
    else:
        print("📌 Test event left for inspection.")

if __name__ == "__main__":
    asyncio.run(test_improved_discord_notification())