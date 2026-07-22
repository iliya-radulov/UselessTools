import os
import pdfplumber
import pandas as pd


def extract_certificate_data(pdf_path):
    """Extract certificate data from a single PDF file."""
    data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            
            if table is None:
                continue
            
            # Skip if table is empty
            if len(table) < 2:
                continue
            
            # First row is header
            for row in table[1:]:
                # Skip empty rows
                if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                    continue
                
                # Adjust column indices based on your PDF's table structure
                # Example: if columns are [Course Name, Topic, Agency, Skills ID]
                course_name = row[0] if len(row) > 0 else ''
                topic = row[1] if len(row) > 1 else ''
                agency = row[2] if len(row) > 2 else ''
                skills_id = row[3] if len(row) > 3 else ''
                
                data.append({
                    'course_name': str(course_name).strip(),
                    'topic': str(topic).strip(),
                    'agency': str(agency).strip(),
                    'skills_id': str(skills_id).strip(),
                    'source_pdf': os.path.basename(pdf_path)
                })
    
    return data


def extract_from_all_pdfs(pdf_folder, output_file='certificates_combined.csv'):
    """Process all PDFs in folder and combine into single DataFrame."""
    all_data = []
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder}")
        return None
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        print(f"Processing: {pdf_file}")
        
        try:
            data = extract_certificate_data(pdf_path)
            all_data.extend(data)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
    
    # Create combined DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        print(f"\n✓ Saved {len(all_data)} certificates to {output_file}")
        
        # Also save to Excel
        excel_file = output_file.replace('.csv', '.xlsx')
        df.to_excel(excel_file, index=False)
        print(f"✓ Saved {len(all_data)} certificates to {excel_file}")
        
        return df
    else:
        print("No data extracted")
        return None


# Usage
if __name__ == "__main__":
    pdf_folder = "/Users/r/Documents/LinkedInLearning/CertificatesDocs/Certificates"  # Change to your folder path
    df = extract_from_all_pdfs(pdf_folder)
    
    if df is not None:
        print("\n=== Sample Data ===")
        print(df.head())
        print(f"\nTotal certificates: {len(df)}")