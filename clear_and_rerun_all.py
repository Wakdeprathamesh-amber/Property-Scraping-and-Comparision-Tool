"""
Clear old data and rerun extraction + comparison for ALL properties
This ensures fresh data is written to sheets with updated logic
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import pandas only when needed (through sheets_manager)
# import pandas as pd  # Not needed here - imported in sheets_manager

def clear_all_extraction_data():
    """Clear all old extraction data from Content_Extraction sheet"""
    print("\n" + "="*80)
    print("STEP 1: CLEARING ALL OLD EXTRACTION DATA")
    print("="*80)
    
    try:
        from src.sheets_manager import SheetsManager
        
        sheets = SheetsManager()
        
        # Clear Content_Extraction sheet
        print("\n📋 Clearing Content_Extraction sheet...")
        try:
            content_df = sheets.read_sheet('Content_Extraction')
            
            if len(content_df) > 0:
                row_count = len(content_df)
                print(f"  Found {row_count} rows in Content_Extraction sheet")
                
                # Clear all data (keep headers)
                worksheet = sheets.workbook.worksheet('Content_Extraction')
                
                # Get headers (pandas DataFrame columns)
                import pandas as pd
                headers = list(content_df.columns)
                
                # Clear and write just headers
                worksheet.clear()
                worksheet.update(values=[headers], range_name='A1')
                
                print(f"  ✅ Cleared {row_count} rows")
                print(f"  Kept headers: {len(headers)} columns")
            else:
                print(f"  ℹ️ Content_Extraction sheet is already empty")
        except Exception as e:
            print(f"  ⚠️ Could not clear Content_Extraction: {e}")
            import traceback
            traceback.print_exc()
        
        # Clear V0_Comparison_Results sheet (data rows only, keep headers)
        print("\n📋 Clearing V0_Comparison_Results sheet...")
        try:
            comparison_df = sheets.read_sheet('V0_Comparison_Results')
            
            if len(comparison_df) > 0:
                row_count = len(comparison_df)
                print(f"  Found {row_count} data rows in V0_Comparison_Results sheet")
                
                worksheet = sheets.workbook.worksheet('V0_Comparison_Results')
                
                # Clear data rows (row 4 onwards, keep 3 header rows)
                # Get total rows
                all_values = worksheet.get_all_values()
                if len(all_values) > 3:
                    # Clear from row 4 onwards
                    worksheet.batch_clear([f'A4:Z{len(all_values)}'])
                    print(f"  ✅ Cleared data rows (kept 3 header rows)")
                else:
                    print(f"  ℹ️ Only header rows exist")
            else:
                print(f"  ℹ️ V0_Comparison_Results sheet is empty")
        except Exception as e:
            print(f"  ⚠️ Could not clear V0_Comparison_Results: {e}")
            # This is okay - comparison will overwrite anyway
        
        print("\n✅ Clearing complete!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Missing dependencies: {e}")
        print("\nPlease install required packages:")
        print("  pip install pandas gspread google-auth")
        return False
    except Exception as e:
        print(f"\n❌ Error clearing data: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_extraction_all():
    """Run extraction for all scraped properties"""
    print("\n" + "="*80)
    print("STEP 2: RUNNING EXTRACTION FOR ALL PROPERTIES")
    print("="*80)
    
    try:
        from run_extraction_step1 import ContentExtractor
        
        extractor = ContentExtractor()
        
        print("\n📋 Processing all scraped properties...")
        stats = extractor.process_all_scraped()
        
        print("\n" + "="*80)
        print("EXTRACTION SUMMARY")
        print("="*80)
        print(f"  Total Properties: {stats['total']}")
        print(f"  ✅ Success: {stats['success']}")
        print(f"  ❌ Failed: {stats['failed']}")
        print("="*80)
        
        if stats['success'] > 0:
            print("\n✅ Extraction complete!")
            return True
        else:
            print("\n⚠️ No properties extracted successfully")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comparison_all():
    """Run V0 comparison for all properties"""
    print("\n" + "="*80)
    print("STEP 3: RUNNING V0 COMPARISON FOR ALL PROPERTIES")
    print("="*80)
    
    try:
        from v0_property_comparison import V0PropertyComparison
        from src.sheets_manager import SheetsManager
        
        comparator = V0PropertyComparison()
        
        # Get property links
        sheets = SheetsManager()
        input_df = sheets.read_sheet('Input_Properties')
        scraped_df = input_df[input_df['Status'] == 'scraped']
        
        property_links = {}
        for idx, row in scraped_df.iterrows():
            property_id = row['Property_ID']
            property_links[property_id] = row.get('Amber_URL', '')
        
        print(f"\n📋 Comparing {len(scraped_df)} properties...")
        
        # Compare all properties
        comparisons = comparator.compare_all_properties(write_to_sheets=True)
        
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        print(f"  ✅ Compared {len(comparisons)} properties")
        print(f"  📊 Results written to V0_Comparison_Results sheet")
        
        # Show sample of results
        if comparisons:
            print("\n📊 Sample Results (first property):")
            print("-"*80)
            first_comp = comparisons[0]
            property_id = first_comp.get('property_id', 'Unknown')
            
            hero_media_amber = first_comp.get('sections', {}).get('Hero & Media', {}).get('amber', {})
            hero_media_uhomes = first_comp.get('sections', {}).get('Hero & Media', {}).get('uhomes', {})
            
            print(f"\n  Property: {property_id}")
            print(f"\n  🔵 AMBER:")
            print(f"    Images:           {hero_media_amber.get('image_count', 0)}")
            print(f"    Videos:           {hero_media_amber.get('video_count', 0)}")
            print(f"    Video Tours:      {hero_media_amber.get('video_tour_count', 0)}")
            print(f"    Virtual Tours:    {hero_media_amber.get('virtual_tour_count', 0)}")
            print(f"    360° Tours:       {hero_media_amber.get('tour_360_count', 0)}")
            print(f"    3D Tours:         {hero_media_amber.get('tour_3d_count', 0)}")
            
            print(f"\n  🟢 UHOMES:")
            print(f"    Images:           {hero_media_uhomes.get('image_count', 0)}")
            print(f"    Videos:           {hero_media_uhomes.get('video_count', 0)}")
            print(f"    Video Tours:      {hero_media_uhomes.get('video_tour_count', 0)}")
            print(f"    Virtual Tours:    {hero_media_uhomes.get('virtual_tour_count', 0)}")
            print(f"    360° Tours:       {hero_media_uhomes.get('tour_360_count', 0)}")
            print(f"    3D Tours:         {hero_media_uhomes.get('tour_3d_count', 0)}")
            print(f"    Lives:            {hero_media_uhomes.get('live_count', 0)}")
            print(f"    By Tenants:       {hero_media_uhomes.get('by_tenant_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_sheets():
    """Verify data is in sheets"""
    print("\n" + "="*80)
    print("STEP 4: VERIFYING DATA IN SHEETS")
    print("="*80)
    
    try:
        from src.sheets_manager import SheetsManager
        import json
        
        sheets = SheetsManager()
        
        # Check Content_Extraction
        print("\n📋 Checking Content_Extraction sheet...")
        content_df = sheets.read_sheet('Content_Extraction')
        
        if len(content_df) == 0:
            print("  ⚠️ Sheet is empty - extraction may have failed")
            return
        
        print(f"  ✅ Found {len(content_df)} rows")
        
        # Count by property
        property_counts = content_df['Property_ID'].value_counts()
        print(f"\n  Properties in sheet: {len(property_counts)}")
        for prop_id, count in property_counts.head(10).items():
            print(f"    {prop_id}: {count} rows")
        
        # Check Hero & Media sections
        hero_media = content_df[content_df['Section_Name'] == 'Hero & Media']
        print(f"\n  Hero & Media sections: {len(hero_media)}")
        
        if len(hero_media) > 0:
            print("\n  📊 Sample Hero & Media Data (first 2):")
            for idx, row in hero_media.head(2).iterrows():
                platform = row.get('Platform', 'Unknown')
                prop_id = row.get('Property_ID', 'Unknown')
                content_json_str = row.get('Content_JSON', '{}')
                
                try:
                    content_json = json.loads(content_json_str) if content_json_str else {}
                    print(f"\n    {prop_id} - {platform.upper()}:")
                    print(f"      Images: {content_json.get('image_count', 0)}")
                    print(f"      Videos: {content_json.get('video_count', 0)}")
                    print(f"      Lives: {content_json.get('live_count', 0)}")
                    print(f"      3D Views: {content_json.get('tour_360_count', 0)}")
                    print(f"      By Tenants: {content_json.get('by_tenant_count', 0)}")
                except:
                    print(f"    {prop_id} - {platform}: Could not parse JSON")
        
        # Check V0_Comparison_Results
        print("\n📋 Checking V0_Comparison_Results sheet...")
        try:
            comparison_df = sheets.read_sheet('V0_Comparison_Results')
            if len(comparison_df) > 0:
                print(f"  ✅ Found {len(comparison_df)} rows in comparison sheet")
                if 'Property_ID' in comparison_df.columns:
                    print(f"  Properties compared: {len(comparison_df['Property_ID'].unique())}")
            else:
                print(f"  ⚠️ Comparison sheet is empty")
        except Exception as e:
            print(f"  ⚠️ Could not read comparison sheet: {e}")
        
        print("\n✅ Verification complete!")
        print("\n💡 Check your Google Sheets to see the updated data:")
        print("   - Content_Extraction sheet: All properties with updated media counts")
        print("   - V0_Comparison_Results sheet: All comparisons with updated counts")
        
    except Exception as e:
        print(f"\n❌ Error verifying sheets: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("\n" + "="*80)
    print("CLEAR AND RERUN EXTRACTION + COMPARISON FOR ALL PROPERTIES")
    print("="*80)
    print("\nThis will:")
    print("1. Clear ALL old extraction data from sheets")
    print("2. Run extraction for ALL scraped properties")
    print("3. Run V0 comparison for ALL properties")
    print("4. Verify data is in sheets")
    print("\n⚠️  This will overwrite all existing data!")
    print("="*80)
    
    # Auto-confirm if running from command line or non-interactive
    import sys
    auto_confirm = False
    
    # Check for --yes flag
    if len(sys.argv) > 1 and sys.argv[1] == '--yes':
        auto_confirm = True
        print("\n✅ Auto-confirmed (--yes flag)")
    
    # Check if running non-interactively (no TTY)
    try:
        import sys
        if not sys.stdin.isatty():
            auto_confirm = True
            print("\n✅ Auto-confirmed (non-interactive mode)")
    except:
        pass
    
    if not auto_confirm:
        # Confirm interactively
        try:
            response = input("\nContinue? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\nCancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️ Non-interactive mode detected. Use --yes flag to auto-confirm.")
            print("Run: python3 clear_and_rerun_all.py --yes")
            return
    
    # Step 1: Clear old data
    if not clear_all_extraction_data():
        print("\n❌ Failed to clear old data. Stopping.")
        return
    
    # Step 2: Run extraction
    if not run_extraction_all():
        print("\n❌ Extraction failed. Stopping.")
        return
    
    # Step 3: Run comparison
    if not run_comparison_all():
        print("\n❌ Comparison failed. Stopping.")
        return
    
    # Step 4: Verify
    verify_sheets()
    
    print("\n" + "="*80)
    print("✅ ALL STEPS COMPLETE!")
    print("="*80)
    print("\n📊 Check your Google Sheets to see the updated counts:")
    print("   - Content_Extraction: All properties with updated media counts")
    print("   - V0_Comparison_Results: All comparisons with updated counts")
    print("\n💡 Key changes:")
    print("   - UHomes: Now uses count fields (96 images, 15 videos, 2 lives, 12 3D, 5 by tenants)")
    print("   - Amber: Now includes room type media (~138 total files)")
    print("   - New fields: live_count, by_tenant_count, tour_360_count, tour_3d_count")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

