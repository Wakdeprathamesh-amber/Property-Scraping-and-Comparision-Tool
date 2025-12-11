"""
Set up column headers for all 6 sheets in Google Sheets
"""

from src.sheets_manager import SheetsManager

def setup_all_headers():
    """Set up headers for all sheets"""
    
    print("=" * 60)
    print("Setting up Google Sheets Headers")
    print("=" * 60)
    
    sheets = SheetsManager()
    
    # Sheet 1: Input_Properties
    print("\n1. Setting up Input_Properties...")
    input_properties_headers = [
        'Property_ID',
        'Amber_URL',
        'Uhomes_URL',
        'Status',
        'Created_At'
    ]
    sheets.setup_headers('Input_Properties', input_properties_headers)
    
    # Sheet 2: Raw_Scraped_Data
    print("\n2. Setting up Raw_Scraped_Data...")
    raw_scraped_headers = [
        'Property_ID',
        'Platform',
        'Property_Name',
        'City',
        'Country',
        'Markdown_Content',
        'Raw_JSON_Data',  # Store raw JSON from API scrapers
        'Metadata_JSON',  # Basic metadata (title, description, images, links)
        # Enhanced structured data fields (separate to avoid truncation)
        'Hero_Features_JSON',  # NEW: Hero features (360 tour, video tour, map, etc.)
        'Payment_Details_JSON',  # NEW: Payment details (installments, deposit, guarantor, etc.)
        'Offers_JSON',  # NEW: Offers/promotions list
        'Nearby_Properties_JSON',  # NEW: Nearby properties list
        'Room_Types_JSON',  # NEW: Room types (for UHomes)
        'Property_Metadata_JSON',  # NEW: Additional property metadata (for Amber)
        'Videos_JSON',  # NEW: Videos list with details
        'Virtual_Tours_JSON',  # NEW: Virtual tours list
        # Counts and summaries
        'Images_Count',
        'Images_URLs',  # First 10 image URLs
        'Videos_Count',
        'Virtual_Tours_Count',
        'Links_Count',
        'Word_Count',
        'Scraper_Used',  # Track which scraper was used (amber_api, uhomes_puppeteer, firecrawl)
        'Scraped_At'
    ]
    sheets.setup_headers('Raw_Scraped_Data', raw_scraped_headers)
    
    # Sheet 3: Section_Scores
    print("\n3. Setting up Section_Scores...")
    section_scores_headers = [
        'Property_ID',
        'Platform',
        'Property_Name',
        'Section_Name',
        'Section_Score',
        'Max_Score',
        'Score_Percentage',
        'Content_Present',
        'Item_Count',
        'Word_Count',
        'Image_Count',
        'Content_Summary',
        'Data_Sources',  # Which data sources were used (api, firecrawl, both)
        'Data_Quality_Score',  # Data quality score (0-100)
        'Detailed_Data_JSON',  # NEW: Full detailed_data as JSON (preserves all analysis data)
        'Sub_Section_Counts_JSON',  # NEW: Structured counts (images, videos, amenities, etc.)
        'Feature_Flags_JSON',  # NEW: Boolean features (360° tour, map toggle, etc.)
        'Items_List_JSON',  # NEW: Exact item lists (amenities, FAQs, room types)
        'Analyzed_At'
    ]
    sheets.setup_headers('Section_Scores', section_scores_headers)
    
    # Sheet 4: Property_Comparisons
    print("\n4. Setting up Property_Comparisons...")
    property_comparisons_headers = [
        'Property_ID',
        'Property_Name',
        'City',
        'Amber_Total_Score',
        'Uhomes_Total_Score',
        'Gap',
        'Winner',
        'Status_Indicator',
        'Amber_Sections_Count',
        'Uhomes_Sections_Count',
        'High_Priority_Actions',
        'Medium_Priority_Actions',
        'Report_Link',
        'Compared_At'
    ]
    sheets.setup_headers('Property_Comparisons', property_comparisons_headers)
    
    # Sheet 5: Insights_Recommendations
    print("\n5. Setting up Insights_Recommendations...")
    insights_headers = [
        'Property_ID',
        'Property_Name',
        'Section_Name',
        'Priority',
        'Current_Score',
        'Potential_Score',
        'Score_Impact',
        'Recommendation',
        'Specific_Actions',
        'Owner_Team',
        'Estimated_Effort',
        'Deadline_Suggestion',
        'Created_At'
    ]
    sheets.setup_headers('Insights_Recommendations', insights_headers)
    
    # Sheet 6: Exclusive_Features
    print("\n6. Setting up Exclusive_Features...")
    exclusive_features_headers = [
        'Property_ID',
        'Property_Name',
        'Feature_Name',
        'Platform_Has_It',
        'Feature_Type',
        'Description',
        'Value_Rating',
        'Recommendation'
    ]
    sheets.setup_headers('Exclusive_Features', exclusive_features_headers)
    
    # Sheet 7: Section_Details (NEW: Detailed subsection storage)
    print("\n7. Setting up Section_Details...")
    try:
        # Try to read the sheet to check if it exists
        sheets.read_sheet('Section_Details')
        print("  Section_Details sheet already exists")
    except ValueError:
        # Sheet doesn't exist, create it
        print("  Creating Section_Details sheet...")
        sheets.create_sheet('Section_Details', rows=10000, cols=26)
        print("  ✅ Section_Details sheet created")
    
    section_details_headers = [
        'Property_ID',
        'Platform',
        'Property_Name',
        'Section_Name',
        'Sub_Section_Name',  # e.g., "Images", "Videos", "Amenities", "FAQs"
        'Item_Type',  # e.g., "amenity", "faq", "room_type", "image", "link"
        'Item_Count',  # Total count for this sub-section
        'Rule_Based_Count',  # Count from rule-based extraction
        'AI_Count',  # Count from AI (for comparison)
        'Count_Source',  # "api", "markdown", "ai", "merged"
        'Items_List_JSON',  # NEW: All items as JSON array (e.g., ["WiFi", "Gym", "Pool"])
        'Items_Details_JSON',  # NEW: Detailed items as JSON array (e.g., [{"name": "WiFi", "type": "common"}, ...])
        'Sub_Score',  # Score for this sub-section if applicable
        'Metadata_JSON',  # Additional metadata as JSON
        'Stored_At'
    ]
    sheets.setup_headers('Section_Details', section_details_headers)
    
    print("\n" + "=" * 60)
    print("✅ All headers set up successfully!")
    print("=" * 60)
    print("\nYou can now view your Google Sheet with proper column headers.")
    print("\nNext steps:")
    print("1. Create CSV template for property input")
    print("2. Build CSV processor")
    print("3. Build scraping engine")

if __name__ == "__main__":
    setup_all_headers()



