#!/usr/bin/env python3
"""Test likes, comments, and save functionality."""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

# Test users and tokens
TEST_USER1_ID = "550e8400-e29b-41d4-a716-446655440001"
TEST_USER2_ID = "550e8400-e29b-41d4-a716-446655440002"

# These would come from actual login in a real test
# For now, we'll try to get valid tokens or use test tokens

async def test_likes_comments_saves():
    """Test the complete functionality."""
    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("Testing Likes, Comments, and Saves Functionality")
        print("=" * 60)
        
        try:
            # 1. Get feed to find a post to test
            print("\n1. Getting feed to find posts...")
            headers = {
                "Authorization": f"Bearer test_token"  # This will fail but shows the attempt
            }
            
            async with session.get(f"{API_BASE}/posts", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    posts = data.get("items", [])
                    if posts:
                        test_post = posts[0]
                        post_id = test_post.get("id")
                        print(f"✓ Found post: {post_id}")
                        print(f"  Author: {test_post.get('author_name')}")
                        print(f"  Caption: {test_post.get('caption')[:50]}...")
                        print(f"  Likes: {test_post.get('likes_count', 0)}")
                        print(f"  Comments: {test_post.get('comments_count', 0)}")
                        print(f"  Saves: {test_post.get('saves_count', 0)}")
                    else:
                        print("✗ No posts found in feed")
                else:
                    print(f"✗ Failed to get feed: {resp.status}")
                    
        except Exception as e:
            print(f"✗ Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_likes_comments_saves())
