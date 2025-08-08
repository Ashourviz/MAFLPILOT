import streamlit as st
import requests
import base64
import io
from PIL import Image
import asyncio
import aiohttp
import time

# Page configuration
st.set_page_config(
    page_title="Change Clothes AI",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def encode_image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def resize_image(image, max_size=1024):
    """Resize image while maintaining aspect ratio"""
    width, height = image.size
    if max(width, height) > max_size:
        ratio = max_size / max(width, height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image

def get_api_key():
    """Get API key from Streamlit secrets"""
    try:
        return st.secrets["API_KEY"]
    except KeyError:
        st.error("🔑 API key not found in secrets. Please contact the administrator.")
        st.stop()

async def call_change_clothes_api_async(model_img_base64, garment_img, category, garment_desc):
    """Async version of the API call using secrets"""
    api_key = get_api_key()
    
    form_data = {
        'modelImg': model_img_base64,
        'garmentImg': garment_img,
        'category': category
    }
    
    if garment_desc and garment_desc.strip():
        form_data['garmentDesc'] = garment_desc.strip()

    api_endpoint = 'https://changeclothesai.online/api/openapi/change-clothes-ai'
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
        }

        # Use aiohttp for async request with longer timeout
        timeout = aiohttp.ClientTimeout(total=180)  # 3 minutes timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Convert to multipart form data
            data = aiohttp.FormData()
            for key, value in form_data.items():
                data.add_field(key, value)
            
            async with session.post(api_endpoint, data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'resultImgUrl': result.get('data', {}).get('resultImgUrl'), 
                        'maskImgUrl': result.get('data', {}).get('maskImgUrl'), 
                        'error': None,
                        'success': True
                    }
                else:
                    error_text = await response.text()
                    return {
                        'resultImgUrl': None, 
                        'maskImgUrl': None, 
                        'error': f'API Error {response.status}: {error_text}',
                        'success': False
                    }

    except asyncio.TimeoutError:
        return {
            'resultImgUrl': None, 
            'maskImgUrl': None, 
            'error': 'Request timed out. The AI is busy, please try again.',
            'success': False
        }
    except Exception as e:
        return {
            'resultImgUrl': None, 
            'maskImgUrl': None, 
            'error': f'Connection error: {str(e)}',
            'success': False
        }

def call_change_clothes_api(model_img_base64, garment_img, category, garment_desc):
    """Synchronous wrapper for the async API call"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        call_change_clothes_api_async(model_img_base64, garment_img, category, garment_desc)
    )

def validate_image_url(url):
    """Validate and load image from URL"""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return None, "URL does not point to an image file"
        
        image = Image.open(io.BytesIO(response.content))
        return image, None
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please check the URL."
    except requests.exceptions.RequestException as e:
        return None, f"Error loading image: {str(e)}"
    except Exception as e:
        return None, f"Invalid image format: {str(e)}"

def main():
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .upload-box {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(45deg, #f8f9ff 0%, #f0f2f6 100%);
    }
    .result-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .category-selector {
        background: linear-gradient(45deg, #f8f9ff 0%, #f0f2f6 100%);
        border-radius: 10px;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>👗 AI Virtual Try-On</h1>
        <p style='font-size: 20px; margin: 0; opacity: 0.9;'>Transform your photos with AI-powered fashion magic!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API key availability (without exposing it)
    try:
        get_api_key()
        api_status = "✅ Ready"
    except:
        st.error("🔑 API configuration error. Please contact support.")
        st.stop()
    
    # Main content area
    col1, col2 = st.columns(2, gap="large")
    
    # Initialize session state
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    with col1:
        st.markdown("### 📷 Upload Model Photo")
        st.markdown("Upload a clear photo of a person (preferably facing forward)")
        
        model_file = st.file_uploader(
            "Choose model image", 
            type=['png', 'jpg', 'jpeg'],
            help="Best results with clear, well-lit photos of people facing forward",
            key="model_upload"
        )
        
        if model_file:
            try:
                model_image = Image.open(model_file)
                
                # Convert to RGB if necessary
                if model_image.mode in ('RGBA', 'P'):
                    model_image = model_image.convert('RGB')
                
                model_image = resize_image(model_image)
                
                with st.container():
                    st.image(model_image, caption="✅ Model Image Ready", use_column_width=True)
                    st.success(f"📏 Size: {model_image.size[0]} × {model_image.size[1]} pixels")
                    
            except Exception as e:
                st.error(f"❌ Error loading model image: {str(e)}")
                model_file = None
    
    with col2:
        st.markdown("### 👕 Choose Garment")
        st.markdown("Provide the clothing item you want to try on")
        
        # Garment input options
        garment_tab1, garment_tab2 = st.tabs(["📁 Upload File", "🌐 Use URL"])
        
        garment_img = None
        garment_display = None
        
        with garment_tab1:
            garment_file = st.file_uploader(
                "Upload garment image", 
                type=['png', 'jpg', 'jpeg'],
                help="Upload a clear image of the clothing item",
                key="garment_file_upload"
            )
            
            if garment_file:
                try:
                    garment_display = Image.open(garment_file)
                    
                    # Convert to RGB if necessary
                    if garment_display.mode in ('RGBA', 'P'):
                        garment_display = garment_display.convert('RGB')
                        
                    garment_display = resize_image(garment_display)
                    garment_img = encode_image_to_base64(garment_display)
                    
                    st.image(garment_display, caption="✅ Garment Image Ready", use_column_width=True)
                    st.success(f"📏 Size: {garment_display.size[0]} × {garment_display.size[1]} pixels")
                    
                except Exception as e:
                    st.error(f"❌ Error loading garment image: {str(e)}")
        
        with garment_tab2:
            garment_url = st.text_input(
                "Enter garment image URL",
                placeholder="https://example.com/shirt.jpg",
                help="Direct link to an image file (jpg, png, etc.)"
            )
            
            if garment_url:
                with st.spinner("Loading image from URL..."):
                    garment_display, error = validate_image_url(garment_url)
                    
                if error:
                    st.error(f"❌ {error}")
                elif garment_display:
                    # Convert to RGB if necessary
                    if garment_display.mode in ('RGBA', 'P'):
                        garment_display = garment_display.convert('RGB')
                        
                    garment_display = resize_image(garment_display)
                    garment_img = garment_url  # Use URL directly for API
                    
                    st.image(garment_display, caption="✅ Garment Image Ready", use_column_width=True)
                    st.success(f"📏 Size: {garment_display.size[0]} × {garment_display.size[1]} pixels")
    
    # Configuration section
    st.markdown("---")
    
    config_col1, config_col2 = st.columns([1, 2])
    
    with config_col1:
        st.markdown("### 🎯 Configuration")
        
        category = st.selectbox(
            "Clothing Category",
            ["upper_body", "lower_body", "dresses"],
            format_func=lambda x: {
                "upper_body": "👕 Upper Body",
                "lower_body": "👖 Lower Body", 
                "dresses": "👗 Dresses"
            }[x],
            help="Select the type of clothing"
        )
        
        # Show category examples
        category_examples = {
            "upper_body": "Shirts, t-shirts, jackets, blouses, sweaters",
            "lower_body": "Pants, jeans, skirts, shorts",
            "dresses": "Full dresses, gowns, robes"
        }
        st.caption(f"Examples: {category_examples[category]}")
    
    with config_col2:
        st.markdown("### ✏️ Description (Optional)")
        garment_desc = st.text_area(
            "Describe the garment for better results",
            placeholder="e.g., A red silk evening dress with golden details",
            help="Be specific about colors, materials, style, etc.",
            max_chars=200,
            height=100
        )
        
        if garment_desc:
            st.caption(f"Characters: {len(garment_desc)}/200")
    
    # Generate section
    st.markdown("---")
    
    # Validation
    can_generate = bool(model_file and garment_img and not st.session_state.processing)
    
    if not can_generate and not st.session_state.processing:
        missing_items = []
        if not model_file:
            missing_items.append("model photo")
        if not garment_img:
            missing_items.append("garment image")
        
        if missing_items:
            st.warning(f"⚠️ Please provide: {' and '.join(missing_items)}")
    
    # Generate button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        if st.button(
            "✨ Generate AI Magic" if can_generate else "⏳ Please provide images above",
            type="primary",
            disabled=not can_generate,
            use_container_width=True
        ):
            st.session_state.processing = True
            
            # Prepare model image
            model_image = Image.open(model_file)
            if model_image.mode in ('RGBA', 'P'):
                model_image = model_image.convert('RGB')
            model_image = resize_image(model_image)
            model_img_base64 = encode_image_to_base64(model_image)
            
            # Progress section
            progress_container = st.empty()
            
            with progress_container.container():
                st.markdown("### 🎨 AI is Creating Your Look...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Enhanced progress simulation
                stages = [
                    ("🔍 Analyzing your photo...", 15),
                    ("👕 Understanding the garment...", 30),
                    ("🧠 AI is thinking creatively...", 50),
                    ("🎨 Generating your new look...", 75),
                    ("✨ Adding final touches...", 90),
                    ("🚀 Almost ready...", 95)
                ]
                
                for stage_text, progress_val in stages:
                    status_text.markdown(f"**{stage_text}**")
                    progress_bar.progress(progress_val)
                    time.sleep(0.8)
                
                status_text.markdown("**🌟 Calling AI API...**")
                
                # API call
                try:
                    result = call_change_clothes_api(
                        model_img_base64, 
                        garment_img, 
                        category, 
                        garment_desc
                    )
                    
                    progress_bar.progress(100)
                    status_text.markdown("**✅ Complete!**")
                    
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    st.session_state.processing = False
                    st.rerun()
            
            # Clear progress
            time.sleep(1)
            progress_container.empty()
            
            # Show results
            if result['error']:
                st.error(f"❌ {result['error']}")
                
                # Helpful error suggestions
                if "timeout" in result['error'].lower():
                    st.info("💡 The AI is very busy right now. Please try again in a moment.")
                elif "401" in result['error'] or "403" in result['error']:
                    st.info("💡 Authentication issue. Please contact support.")
                elif "400" in result['error']:
                    st.info("💡 Please check your image formats and try again.")
                else:
                    st.info("💡 Please try again. If the problem persists, contact support.")
                    
            else:
                # Success! Show results
                st.balloons()
                st.success("🎉 Your AI-generated look is ready!")
                
                # Results display
                st.markdown("### ✨ Your Transformation")
                
                if result['resultImgUrl']:
                    # Before and after comparison
                    comparison_col1, comparison_col2 = st.columns(2)
                    
                    with comparison_col1:
                        st.markdown("**👤 Original**")
                        st.image(model_image, use_column_width=True)
                    
                    with comparison_col2:
                        st.markdown("**✨ With New Outfit**")
                        st.image(result['resultImgUrl'], use_column_width=True)
                
                # Download section
                st.markdown("### 📥 Download Your Results")
                
                download_col1, download_col2 = st.columns(2)
                
                with download_col1:
                    if result['resultImgUrl']:
                        st.markdown("**🎨 Final Result**")
                        st.image(result['resultImgUrl'], use_column_width=True)
                        st.markdown(f"[⬇️ Download Final Image]({result['resultImgUrl']})")
                
                with download_col2:
                    if result['maskImgUrl']:
                        st.markdown("**🎭 Processing Mask**")
                        st.image(result['maskImgUrl'], use_column_width=True)
                        st.markdown(f"[⬇️ Download Mask Image]({result['maskImgUrl']})")
                
                # Social sharing suggestion
                st.markdown("---")
                st.info("🎉 Love your new look? Share it with friends and try more outfits!")
            
            st.session_state.processing = False

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 15px; margin-top: 2rem;'>
        <h3 style='color: #4a5568; margin-bottom: 10px;'>✨ AI Fashion Technology</h3>
        <p style='color: #718096; margin: 0;'>Experience the future of virtual try-on with advanced AI</p>
        <small style='color: #a0aec0;'>Powered by Change Clothes AI • Built with ❤️</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
