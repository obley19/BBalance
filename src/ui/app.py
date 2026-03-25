import streamlit as st
import time
import pandas as pd
import sys
import os

# Adds the project root to sys.path so 'src' can be correctly imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.search.engine import SearchEngine

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Digital Curator | E-Commerce Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Manrope', sans-serif;
    }

    .stApp {
        background-color: #f8fafc;
    }

    /* Search Bar Styling */
    .search-container {
        margin-top: -2rem;
        margin-bottom: 2rem;
    }
    
    /* Product Card Styling */
    .product-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #1A94FF;
    }

    .product-image {
        width: 100%;
        height: 200px;
        object-fit: contain;
        border-radius: 8px;
        margin-bottom: 1rem;
        background: #f1f5f9;
    }

    .platform-badge {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 2px 8px;
        border-radius: 4px;
        color: white;
        width: fit-content;
        margin-bottom: 0.5rem;
    }

    .shopee { background-color: #EE4D2D; }
    .tiki { background-color: #1A94FF; }
    .chotot { background-color: #FFBA00; color: #1e293b; }
    .ebay { background-color: #86B817; }

    .product-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 3rem;       /* Sửa thành min-height: 3rem để đủ chỗ 2 dòng */
        line-height: 1.5;
    }

    .product-price {
        font-size: 1.2rem;
        font-weight: 800;
        color: #1A94FF;
        margin-top: auto;
    }

    .product-meta {
        font-size: 0.8rem;
        color: #64748b;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;  /* Chỉnh từ center thành flex-end */
        margin-top: 0.5rem;
        min-height: 2.5rem;     /* Cho meta 1 khoảng an toàn 2 dòng */
    }

    .product-category {
        display: -webkit-box;
        -webkit-line-clamp: 2;  /* Giới hạn category dài xuống 2 dòng, cắt đuôi gạch... */
        -webkit-box-orient: vertical;
        overflow: hidden;
        padding-right: 8px;
        flex: 1;
    }

    .score-badge {
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 600;
    }

    .buy-btn {
        display: block;
        text-align: center;
        background: #f1f5f9;
        color: #475569;
        padding: 8px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 600;
        margin-top: 1rem;
        transition: background 0.2s;
    }

    .buy-btn:hover {
        background: #e2e8f0;
        color: #1e293b;
    }

    /* Sidebar Tweaks */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }

    /* Hide Streamlit components if needed */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- UTILITIES ---
def format_currency(value):
    if value == 0:
        return "Liên hệ"
    return f"{value:,.0f}₫".replace(",", ".")

# --- BACKEND INITIALIZATION ---
@st.cache_resource
def get_search_engine():
    engine = SearchEngine(
        index_dir="data/index", 
        data_path="data/MASTER_DATA_CLEAN.jsonl", 
        search_mode="bm25", 
        vector_index_dir="data/vector_index"
    )
    engine.load()
    return engine

# --- SESSION STATE ---
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# --- APP ---
def main():
    local_css()
    engine = get_search_engine()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("Curated Search")
        st.caption("Precision Filtering & Settings")
        
        st.divider()
        
        # Search Mode
        search_mode = st.radio(
            "Search Mode",
            ["BM25 Lexical", "Vector Semantic", "Hybrid Search"],
            index=0,
            help="BM25 for keyword match, Vector for semantics, Hybrid for both."
        )
        if "BM25" in search_mode:
            mode_key = "bm25"
        elif "Vector" in search_mode:
            mode_key = "vector"
        else:
            mode_key = "hybrid"
            
        engine.set_search_mode(mode_key)
        
        # Platform Filter
        st.subheader("Platforms")
        selected_platforms = []
        platforms = {
            "Shopee": "shopee",
            "Tiki": "tiki",
            "Chợ Tốt": "chotot",
            "eBay": "ebay"
        }
        for label, key in platforms.items():
            if st.checkbox(label, value=True):
                selected_platforms.append(key)
        
        # Price Range
        st.subheader("Price Range")
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Min Price", min_value=0, step=100000)
        with col2:
            max_price = st.number_input("Max Price", min_value=0, step=100000, value=100000000)
            
        # Sorting
        st.subheader("Sort By")
        sort_option = st.selectbox(
            "Order",
            ["Mặc định", "Price: Low to High", "Price: High to Low"]
        )
        
        st.divider()
        
        # History
        st.subheader("Recent Searches")
        for q in st.session_state.search_history[:10]:
            if st.button(f"🔍 {q}", key=f"hist_{q}", use_container_width=True):
                st.session_state.query = q # Trigger search for this query
        
        if st.button("Clear All Filters", use_container_width=True, type="secondary"):
            st.rerun()

    # --- MAIN CONTENT ---
    st.markdown('<h1 style="text-align: center; color: #1e293b; margin-bottom: 0;">Digital Curator</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #64748b; font-size: 1.1rem;">Modern E-Commerce Search Engine</p>', unsafe_allow_html=True)
    
    # Search Input
    query = st.text_input("", placeholder="Search for products (e.g., iPhone 15 Pro Max)...", key="search_input", label_visibility="collapsed")
    
    if query:
        # Add to history
        if query not in st.session_state.search_history:
            st.session_state.search_history.insert(0, query)
        
        # Query Expansion
        expanded = engine.expand_query(query)
        if expanded.lower() != query.lower():
            st.info(f"Showing results for **{expanded}** (expanded from '{query}')")
            query_to_search = expanded
        else:
            query_to_search = query
            
        # Search Execution
        start_time = time.time()
        raw_results = engine.search(query_to_search, top_k=50)
        latency = (time.time() - start_time) * 1000
        
        # Client-side filtering
        filtered_results = [
            r for r in raw_results 
            if r['platform'] in selected_platforms 
            and (min_price <= r['price'] <= max_price or r['price'] == 0)
        ]
        
        # Sorting
        if sort_option == "Price: Low to High":
            filtered_results = sorted(filtered_results, key=lambda x: x['price'])
        elif sort_option == "Price: High to Low":
            filtered_results = sorted(filtered_results, key=lambda x: x['price'], reverse=True)
        # Else default to score (engine returns sorted by score)
        
        # Results Info
        st.write(f"Found {len(filtered_results)} results in {latency:.1f}ms")
        
        # Pagination
        items_per_page = 12
        num_pages = (len(filtered_results) // items_per_page) + (1 if len(filtered_results) % items_per_page > 0 else 0)
        
        if num_pages > 0:
            page = st.number_input("Page", min_value=1, max_value=num_pages, step=1)
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            page_results = filtered_results[start_idx:end_idx]
            
            # Grid Display
            cols = st.columns(4)
            for i, item in enumerate(page_results):
                with cols[i % 4]:
                    price_display = format_currency(item['price'])
                    platform_class = item['platform'].lower().replace(" ", "")
                    
                    card_html = f"""
                    <div class="product-card">
                        <div>
                            <div class="platform-badge {platform_class}">{item['platform']}</div>
                            <div class="product-title">{item['title']}</div>
                            <div class="product-meta">
                                <span class="product-category" title="{item.get('category', 'Generic')}">{item.get('category', 'Generic')}</span>
                                <span class="score-badge">⭐ {item.get('bm25_score', 0):.1f}</span>
                            </div>
                        </div>
                        <div>
                            <div class="product-price">{price_display}</div>
                            <a href="{item['link']}" target="_blank" class="buy-btn">View Product</a>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.warning("No results found matching your filters. Try adjusting price range or platforms.")
    else:
        # Welcome State
        st.container()
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem; background: white; border-radius: 20px; border: 2px dashed #e2e8f0; margin-top: 2rem;">
            <h2 style="color: #64748b;">Ready to find the best deals?</h2>
            <p style="color: #94a3b8;">Enter a product name above to start searching across Shopee, Tiki, Chợ Tốt, and eBay.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
