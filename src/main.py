from converter import WebpagePDFConverter
import sys

def main():
    print("Webpage to PDF Converter")
    print("-----------------------")
    
    try:
        url = input("Enter the website URL: ")
        max_depth = int(input("Enter maximum crawl depth (1-5): "))
        output_file = input("Enter output PDF filename: ")
        
        if not output_file.endswith('.pdf'):
            output_file += '.pdf'
            
        if max_depth < 1 or max_depth > 5:
            print("Crawl depth must be between 1 and 5")
            sys.exit(1)
            
        converter = WebpagePDFConverter(url, max_depth)
        converter.crawl_and_convert(url)
        converter.save_pdf(output_file)
        
    except ValueError as e:
        print("Error: Please enter a valid number for crawl depth")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()