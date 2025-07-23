import random
import string
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import json
from gtts import gTTS
import tempfile
import math
import requests

class CaptchaGenerator:
    def __init__(self):
        self.width = 200
        self.height = 80
        self.font_size = 36
        self.noise_level = 50
        
    def generate_text_captcha(self, length=5):
        """Generate random text for CAPTCHA"""
        # Use numbers and uppercase letters (avoiding confusing characters)
        chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_math_captcha(self):
        """Generate simple math problem for CAPTCHA"""
        operations = ['+', '-', '*']
        operation = random.choice(operations)
        
        if operation == '+':
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            answer = a + b
            question = f"{a} + {b}"
        elif operation == '-':
            a = random.randint(10, 30)
            b = random.randint(1, a-1)
            answer = a - b
            question = f"{a} - {b}"
        else:  # multiplication
            a = random.randint(2, 9)
            b = random.randint(2, 9)
            answer = a * b
            question = f"{a} × {b}"
        
        return question, str(answer)
    
    def create_image_captcha(self, text, captcha_type='text'):
        """Create image CAPTCHA"""
        # Create image
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Add background noise
        for _ in range(self.noise_level):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # Add noise lines
        for _ in range(5):
            start = (random.randint(0, self.width), random.randint(0, self.height))
            end = (random.randint(0, self.width), random.randint(0, self.height))
            draw.line([start, end], fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)), width=1)
        
        # Try to load a font, fallback to default if not available
        try:
            # Try to use a system font
            font_paths = [
                '/System/Library/Fonts/Arial.ttf',  # macOS
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
                'C:\\Windows\\Fonts\\arial.ttf',  # Windows
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, self.font_size)
                    break
            
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        
        # Add text with slight rotation and distortion
        for i, char in enumerate(text):
            char_x = x + i * (text_width // len(text))
            char_y = y + random.randint(-5, 5)
            
            # Random color for each character
            color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
            
            # Create temporary image for character rotation
            char_img = Image.new('RGBA', (50, 50), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((10, 10), char, font=font, fill=color)
            
            # Rotate character slightly
            angle = random.randint(-15, 15)
            rotated = char_img.rotate(angle, expand=1)
            
            # Paste rotated character
            image.paste(rotated, (char_x, char_y), rotated)
        
        # Convert to base64
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def create_audio_captcha(self, text):
        """Create audio CAPTCHA - Currently disabled due to dependency issues"""
        return None  # Temporarily disabled
    
    def create_simple_audio_captcha(self, text):
        """Create simple audio CAPTCHA - Currently disabled due to dependency issues"""
        return None  # Temporarily disabled

class RecaptchaManager:
    def __init__(self, site_key, secret_key):
        self.site_key = site_key
        self.secret_key = secret_key
        self.verify_url = "https://www.google.com/recaptcha/api/siteverify"
    
    def verify_recaptcha_v2(self, response_token, remote_ip=None):
        """Verify reCAPTCHA v2 response"""
        try:
            data = {
                'secret': self.secret_key,
                'response': response_token
            }
            
            if remote_ip:
                data['remoteip'] = remote_ip
            
            response = requests.post(self.verify_url, data=data, timeout=10)
            result = response.json()
            
            return {
                'success': result.get('success', False),
                'score': None,  # v2 doesn't have score
                'action': None,  # v2 doesn't have action
                'challenge_ts': result.get('challenge_ts'),
                'hostname': result.get('hostname'),
                'error_codes': result.get('error-codes', [])
            }
            
        except Exception as e:
            print(f"Error verifying reCAPTCHA v2: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_recaptcha_v3(self, response_token, expected_action, min_score=0.5, remote_ip=None):
        """Verify reCAPTCHA v3 response"""
        try:
            data = {
                'secret': self.secret_key,
                'response': response_token
            }
            
            if remote_ip:
                data['remoteip'] = remote_ip
            
            response = requests.post(self.verify_url, data=data, timeout=10)
            result = response.json()
            
            success = result.get('success', False)
            score = result.get('score', 0)
            action = result.get('action', '')
            
            # Check if action matches and score is above threshold
            action_valid = action == expected_action if expected_action else True
            score_valid = score >= min_score
            
            return {
                'success': success and action_valid and score_valid,
                'score': score,
                'action': action,
                'challenge_ts': result.get('challenge_ts'),
                'hostname': result.get('hostname'),
                'error_codes': result.get('error-codes', []),
                'action_valid': action_valid,
                'score_valid': score_valid
            }
            
        except Exception as e:
            print(f"Error verifying reCAPTCHA v3: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def generate_captcha_challenge(captcha_type='text'):
    """Generate CAPTCHA challenge"""
    generator = CaptchaGenerator()
    
    if captcha_type == 'math':
        question, answer = generator.generate_math_captcha()
        image_data = generator.create_image_captcha(question, 'math')
        audio_data = generator.create_audio_captcha(question)
        
        return {
            'type': 'math',
            'question': question,
            'answer': answer,
            'image': image_data,
            'audio': audio_data
        }
    else:  # text captcha
        text = generator.generate_text_captcha()
        image_data = generator.create_image_captcha(text, 'text')
        audio_data = generator.create_audio_captcha(text)
        
        return {
            'type': 'text',
            'question': text,
            'answer': text,
            'image': image_data,
            'audio': audio_data
        }

def verify_captcha(user_input, correct_answer):
    """Verify CAPTCHA response"""
    if not user_input or not correct_answer:
        return False
    
    # Case-insensitive comparison
    return user_input.strip().upper() == correct_answer.strip().upper()

def create_recaptcha_manager(site_key, secret_key):
    """Create reCAPTCHA manager instance"""
    return RecaptchaManager(site_key, secret_key)
