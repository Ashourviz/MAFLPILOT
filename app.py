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
    initial_sidebar_state="expanded"
)

def encode_image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
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

async def call_change_clothes_api_async(model_img_base64, garment_img, category, garment_desc, api_key):
    """Async version of the API call"""
    form_data = {
        'modelImg': model_img_base64,
        'garmentImg': garment_img,
        'category': category
    }
    
    if garment_desc:
        form_data['garmentDesc'] = garment_desc

    api_endpoint = 'https://changeclothesai.online/api/openapi/change-clothes-ai'
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
        }

        # Use aiohttp for async request
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
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
                        'error': None
                    }
                else:
                    error_text = await response.text()
                    return {
                        'resultImgUrl': None, 
                        'maskImgUrl': None, 
                        'error': f'HTTP {response.status}: {error_text}'
                    }

    except Exception as e:
        return {
            'resultImgUrl': None, 
            'maskImgUrl': None, 
            'error': str(e)
        }

def call_change_clothes_api(model_img_base64, garment_img, category, garment_desc, api_key):
    """Synchronous wrapper for the async API call"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        call_change_clothes_api_async(model_img_base64, garment_img, category, garment_desc, api_key)
    )

def main():
    # Header with custom styling
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>👗 Change Clothes AI</h1>
        <p style='font-size: 18px; color: #666;'>Transform your photos with AI-powered virtual try-on technology!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .uploadedFile {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar for API configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input with help
        api_key = st.text_input(
            "API Key", 
            type="password", 
            help="Enter your Change Clothes AI API key from changeclothesai.online",
            placeholder="your_api_key_here"
        )
        
        if not api_key:
            st.warning("⚠️ Please enter your API key to continue")
            st.info("Get your API key from [changeclothesai.online](https://changeclothesai.online)")
        
        st.markdown("---")
        
        # Instructions
        st.header("📋 How to Use")
        st.markdown("""
        **Step by step:**
        1. 📸 Upload a model image (person photo)
        2. 👕 Provide a garment image (URL or upload)
        3. 🎯 Select the clothing category
        4. ✏️ Add an optional description
        5. ✨ Click 'Generate New Look'
        
        **Tips for best results:**
        - Use clear, well-lit photos
        - Ensure the person is facing forward
        - Choose high-quality garment images
        - Be specific in descriptions
        """)
        
        st.markdown("---")
        
        # About section
        with st.expander("ℹ️ About"):
            st.markdown("""
            This app uses AI to virtually try on clothes. Upload a photo of a person 
            and a garment, and see how they would look together!
            
            **Supported categories:**
            - Upper body (shirts, jackets, tops)
            - Lower body (pants, skirts)
            - Dresses (full dresses)
            """)
    
    # Check if API key is provided
    if not api_key:
        st.info("👈 Please enter your API key in the sidebar to get started!")
        return
    
    # Main content area
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.header("📷 Model Image")
        st.markdown("Upload a clear photo of a person")
        
        model_file = st.file_uploader(
            "Choose model image", 
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear photo of a person (preferably facing forward)"
        )
        
        if model_file:
            model_image = Image.open(model_file)
            model_image = resize_image(model_image)
            st.image(model_image, caption="Model Image", use_column_width=True)
            
            # Show image info
            st.caption(f"📏 Size: {model_image.size[0]} × {model_image.size[1]} pixels")
    
    with col2:
        st.header("👕 Garment Image")
        st.markdown("Provide the clothing item to try on")
        
        # Option to choose between URL or file upload
        garment_option = st.radio(
            "Choose garment source:",
            ["📁 Upload File", "🌐 Use URL"],
            horizontal=True
        )
        
        garment_img = None
        garment_display = None
        
        if garment_option == "📁 Upload File":
            garment_file = st.file_uploader(
                "Choose garment image", 
                type=['png', 'jpg', 'jpeg'],
                key="garment_upload",
                help="Upload an image of the clothing item"
            )
            if garment_file:
                garment_display = Image.open(garment_file)
                garment_display = resize_image(garment_display)
                garment_img = encode_image_to_base64(garment_display)
                st.image(garment_display, caption="Garment Image", use_column_width=True)
                st.caption(f"📏 Size: {garment_display.size[0]} × {garment_display.size[1]} pixels")
        else:
            garment_url = st.text_input(
                "Garment image URL",
                placeholder="https://example.com/garment.jpg",
                help="Enter a direct link to the garment image"
            )
            if garment_url:
                try:
                    with st.spinner("Loading image from URL..."):
                        response = requests.get(garment_url, timeout=10)
                        response.raise_for_status()
                        garment_display = Image.open(io.BytesIO(response.content))
                        garment_display = resize_image(garment_display)
                        garment_img = garment_url
                        st.image(garment_display, caption="Garment Image", use_column_width=True)
                        st.caption(f"📏 Size: {garment_display.size[0]} × {garment_display.size[1]} pixels")
                except Exception as e:
                    st.error(f"❌ Error loading image from URL: {e}")
                    st.info("💡 Make sure the URL is a direct link to an image file")
    
    # Configuration options
    st.markdown("---")
    st.header("🎯 Configuration")
    
    col3, col4 = st.columns(2)
    
    with col3:
        category = st.selectbox(
            "Clothing Category",
            ["upper_body", "lower_body", "dresses"],
            format_func=lambda x: {
                "upper_body": "👕 Upper Body (shirts, jackets, tops)",
                "lower_body": "👖 Lower Body (pants, skirts)", 
                "dresses": "👗 Dresses (full dresses)"
            }[x],
            help="Select the type of clothing to try on"
        )
    
    with col4:
        garment_desc = st.text_input(
            "Garment Description (Optional)",
            placeholder="e.g., A beautiful red evening dress",
            help="Describe the garment for better AI understanding"
        )
    
    # Generate button
    st.markdown("---")
    
    # Validation before showing button
    can_generate = bool(model_file and garment_img and api_key)
    
    if not can_generate:
        missing_items = []
        if not model_file:
            missing_items.append("Model image")
        if not garment_img:
            missing_items.append("Garment image")
        if not api_key:
            missing_items.append("API key")
        
        st.warning(f"⚠️ Missing: {', '.join(missing_items)}")
    
    generate_button = st.button(
        "✨ Generate New Look", 
        type="primary", 
        use_container_width=True,
        disabled=not can_generate,
        help="Click to start the AI transformation!" if can_generate else "Please provide all required inputs"
    )
    
    if generate_button and can_generate:
        # Prepare model image
        model_image = Image.open(model_file)
        model_image = resize_image(model_image)
        model_img_base64 = encode_image_to_base64(model_image)
        
        # Show progress with more detailed steps
        progress_container = st.container()
        with progress_container:
            st.info("🎨 AI is working its magic... This may take 30-60 seconds")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress stages
            stages = [
                "🔍 Analyzing model image...",
                "👕 Processing garment...",
                "🧠 AI thinking...",
                "🎨 Generating new look...",
                "✨ Finalizing results..."
            ]
            
            for i, stage in enumerate(stages):
                status_text.text(stage)
                for j in range(20):
                    progress_bar.progress((i * 20 + j + 1))
                    time.sleep(0.05)
            
            status_text.text("🚀 Calling API...")
            
            # Call API
            try:
                result = call_change_clothes_api(
                    model_img_base64, 
                    garment_img, 
                    category, 
                    garment_desc, 
                    api_key
                )
                
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                return
        
        # Clear progress after completion
        progress_container.empty()
        
        # Display results
        if result['error']:
            st.error(f"❌ Error: {result['error']}")
            
            # Help with common errors
            if "401" in str(result['error']):
                st.info("💡 Check your API key - it might be invalid or expired")
            elif "400" in str(result['error']):
                st.info("💡 Check your image formats and sizes")
            elif "timeout" in str(result['error']).lower():
                st.info("💡 The API is taking longer than usual. Please try again.")
        else:
            st.success("🎉 Successfully generated new look!")
            
            # Display results with better layout
            st.header("✨ Your AI-Generated Results")
            
            if result['resultImgUrl'] or result['maskImgUrl']:
                
                # Show original vs result comparison
                if result['resultImgUrl']:
                    st.subheader("👀 Before & After Comparison")
                    comp_col1, comp_col2 = st.columns(2)
                    
                    with comp_col1:
                        st.markdown("**Original**")
                        st.image(model_image, use_column_width=True)
                    
                    with comp_col2:
                        st.markdown("**With New Outfit**")
                        st.image(result['resultImgUrl'], use_column_width=True)
                
                # Detailed results
                st.subheader("📥 Download Results")
                result_col1, result_col2 = st.columns(2)
                
                with result_col1:
                    if result['resultImgUrl']:
                        st.markdown("**🎨 Final Result**")
                        st.image(result['resultImgUrl'], use_column_width=True)
                        st.markdown(f"[⬇️ Download Result Image]({result['resultImgUrl']})")
                
                with result_col2:
                    if result['maskImgUrl']:
                        st.markdown("**🎭 Processing Mask**")
                        st.image(result['maskImgUrl'], use_column_width=True)
                        st.markdown(f"[⬇️ Download Mask Image]({result['maskImgUrl']})")
                
                # Success message with social sharing suggestion
                st.balloons()
                st.success("🎉 Love your new look? Share it with friends!")
                
            else:
                st.warning("⚠️ No result images returned from the API")
                st.info("This might be a temporary issue. Please try again.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
        <h4>💝 Made with ❤️ using Streamlit</h4>
        <p>Powered by <a href="https://changeclothesai.online" target="_blank">Change Clothes AI</a></p>
        <p><small>© 2025 Change Clothes AI App. Transform your style with AI!</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
