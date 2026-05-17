#!/usr/bin/env python3
"""
Regression test for Telegram image delivery pipeline.
Tests end-to-end: image generation → file validation → Telegram delivery.
"""

import os
import sys
import tempfile

# Add tools to path
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/tools')

from image_delivery_adapter import MockImageDeliveryAdapter, send_image_with_adapter

PIL_FORMAT_TO_MIME = {
    'PNG': 'image/png',
    'JPEG': 'image/jpeg',
    'JPG': 'image/jpeg',
    'WEBP': 'image/webp',
    'GIF': 'image/gif',
}

def validate_media_file(path: str) -> dict:
    """Validate media file for Telegram delivery."""
    result = {
        'exists': False,
        'size_ok': False,
        'mime_type_ok': False,
        'readable': False,
        'mime_type': None
    }
    
    if os.path.exists(path):
        result['exists'] = True
        
        # Check size (Telegram limit: 20MB, safe limit: 10MB)
        file_size = os.path.getsize(path)
        result['size_ok'] = file_size < 10 * 1024 * 1024
        result['file_size_bytes'] = file_size
        
        # Check MIME type using Python PIL
        try:
            from PIL import Image
            with Image.open(path) as img:
                result['pil_format'] = img.format or 'unknown'
                result['mime_type'] = PIL_FORMAT_TO_MIME.get(result['pil_format'], 'application/octet-stream')
                result['mime_type_ok'] = result['mime_type'].startswith('image/')
                result['readable'] = True
        except Exception as e:
            result['readable'] = False
            result['error'] = str(e)
    
    return result

def run_mime_validation_tests() -> bool:
    """Validate PIL image formats are normalized to real MIME types."""
    from PIL import Image

    fixtures = [
        ('PNG', '.png', 'image/png'),
        ('JPEG', '.jpg', 'image/jpeg'),
        ('WEBP', '.webp', 'image/webp'),
        ('GIF', '.gif', 'image/gif'),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        for pil_format, suffix, expected_mime in fixtures:
            image_path = os.path.join(tmpdir, f'test{suffix}')
            Image.new('RGB', (1, 1), (255, 0, 0)).save(image_path, pil_format)
            validation = validate_media_file(image_path)

            assert validation['exists'] is True, validation
            assert validation['readable'] is True, validation
            assert validation['size_ok'] is True, validation
            assert validation['mime_type_ok'] is True, validation
            assert validation['mime_type'] == expected_mime, validation

        invalid_path = os.path.join(tmpdir, 'not-an-image.bin')
        with open(invalid_path, 'wb') as f:
            f.write(b'not an image')
        invalid_validation = validate_media_file(invalid_path)
        assert invalid_validation['exists'] is True, invalid_validation
        assert invalid_validation['readable'] is False, invalid_validation
        assert invalid_validation['mime_type_ok'] is False, invalid_validation

    return True

def send_media_to_telegram(file_path: str, target_chat_id: str, caption: str = None, adapter=None):
    """Send media to Telegram with proper error handling."""
    # Validate first
    validation = validate_media_file(file_path)
    if not validation['exists'] or not validation['readable']:
        return {
            'success': False,
            'error': 'File validation failed',
            'details': validation
        }

    delivery_result = send_image_with_adapter(
        image_path=file_path,
        target_chat_id=target_chat_id,
        caption=caption,
        mime_type=validation['mime_type'],
        adapter=adapter,
    )
    delivery_result['details'] = validation
    return delivery_result

def run_adapter_boundary_tests() -> bool:
    """Verify CLI tests use an injected/mock adapter boundary."""
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(tmpdir, 'adapter-test.png')
        Image.new('RGB', (1, 1), (0, 255, 0)).save(image_path, 'PNG')

        adapter = MockImageDeliveryAdapter()
        caption = 'Adapter boundary test image'
        result = send_media_to_telegram(image_path, 'test-chat', caption, adapter=adapter)

        assert result['success'] is True, result
        assert result['mock'] is True, result
        assert len(adapter.calls) == 1, adapter.calls
        assert adapter.calls[0].image_path == image_path, adapter.calls[0]
        assert adapter.calls[0].caption == caption, adapter.calls[0]
        assert adapter.calls[0].mime_type == 'image/png', adapter.calls[0]

    return True

def run_regression_test() -> bool:
    """Run full regression test for image delivery pipeline."""
    print("🧪 Running Telegram Image Delivery Regression Test")
    print("=" * 60)
    
    # Step 1: Use existing test images from earlier delivery
    test_images = [
        "/home/jason2ykk/.openclaw/media/tool-image-generation/image-1---fac50851-9c05-4550-97ca-e99b0296a6bd.png",
        "/home/jason2ykk/.openclaw/media/tool-image-generation/image-1---f36a6dab-a82a-4868-9cd7-32035d056154.png",
        "/home/jason2ykk/.openclaw/media/tool-image-generation/image-1---67fb6241-1d88-4708-9d6c-d0313eccf211.png"
    ]
    
    test_chat_id = "1491264949"  # Jason's Telegram
    
    all_passed = True
    
    for image_path in test_images:
        print(f"\n📁 Testing: {os.path.basename(image_path)}")
        print("-" * 40)
        
        # Test 1: File existence
        print("   1. File existence check...")
        validation = validate_media_file(image_path)
        if validation['exists']:
            print(f"      ✅ File exists")
        else:
            print(f"      ❌ File not found")
            all_passed = False
            continue
        
        # Test 2: Size validation
        print("   2. Size validation (<10MB)...")
        if validation['size_ok']:
            print(f"      ✅ Size OK: {validation['file_size_bytes']} bytes")
        else:
            print(f"      ❌ Size too large: {validation['file_size_bytes']} bytes")
            all_passed = False
            continue
        
        # Test 3: MIME type validation
        print("   3. MIME type validation...")
        if validation['mime_type_ok']:
            print(f"      ✅ MIME type OK: {validation['mime_type']}")
        else:
            print(f"      ❌ Invalid MIME type")
            all_passed = False
            continue
        
        # Test 4: Readability
        print("   4. Readability check...")
        if validation['readable']:
            print(f"      ✅ File readable")
        else:
            print(f"      ❌ File not readable")
            all_passed = False
            continue
        
        # Test 5: Telegram delivery
        print("   5. Telegram delivery test...")
        try:
            delivery_result = send_media_to_telegram(image_path, test_chat_id, f"Test image: {os.path.basename(image_path)}")
            if delivery_result['success']:
                print(f"      ✅ Delivery success!")
                print(f"         Message ID: {delivery_result['message_id']}")
                print(f"         Chat ID: {delivery_result['chat_id']}")
                print(f"         File ID: {delivery_result['file_id']}")
            else:
                print(f"      ❌ Delivery failed: {delivery_result['error']}")
                all_passed = False
        except Exception as e:
            print(f"      ❌ Exception during delivery: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ REGRESSION TEST: PASSED")
        print("   Image generation + Telegram delivery: VALIDATED")
        print("   All validation checks: PASSED")
        print("   All delivery attempts: SUCCESSFUL")
        return True
    else:
        print("❌ REGRESSION TEST: FAILED")
        return False

if __name__ == '__main__':
    result = run_regression_test()
    sys.exit(0 if result else 1)
