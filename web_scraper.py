from bs4 import BeautifulSoup as soup
import datetime
import pandas as pd
import re
import requests

# -----------------------------------
# Define global variables
# -----------------------------------

# Identify base URL
base_url_for_category = "https://books.toscrape.com/"
base_url_for_book = "https://books.toscrape.com/catalogue/"

# Get the date of scrapping
scraping_date = datetime.date.today()

# Create a dictionary to convert words to digits
# We will use it when fetching rating
w_to_d = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

# Create a list to store all the extracted items
books_all =[]


# -----------------------------------
# Define 'main' function
# -----------------------------------
def main():
    # ----------------------------------------------------------
    #           RETRIEVE WEBSITE AND PARSE HTML
    # ----------------------------------------------------------
    
    # Identify the target website's address, i.e., URL
    books_url = "https://books.toscrape.com/index.html"

    # Create a response object to get the web page's HTML content
    get_url = requests.get(books_url)

    # Create a 'BeautifulSoup' object to parse HTML text with the help
    # of the 'html.parser'
    books_soup = soup(get_url.text, "html.parser")

    # Check website's response
    # - 200: Target website has replied it’s ok to connect
    # - 403: Request is legal, but the server is refusing to respond to it
    # - 404: Requested page not found, it may be available again in the future. 
    # print(get_url)

    # Get some intuition by printing out HTML
    # This setup is not required to build a web scraper
    # print(get_url.text)
    # print(books_soup)
    # Use 'prettify' method to make HTML be nicely formatted
    # print(books_soup.prettify())

    # ----------------------------------------------------------
    #           EXTRACT, CLEAN, AND STORE DATA
    # ----------------------------------------------------------
    
    # Fetch all the books
    fetch_all_books(books_soup)

    # ----------------------------------------------------------
    #                       SAVE DATA
    # ----------------------------------------------------------
    output(books_all)


# -----------------------------------
# Define functions below
# -----------------------------------
def find_categories(soup_object):
    """
    Find all categories
    """
    categories = soup_object.find("ul", {"class": "nav nav-list"}).\
                                find("li").find("ul").find_all("li")
    
    return categories


def fetch_books_by_category(category_name, category):
    """
    Fetch books by category
    Scrape all the books listed on one page
    Go to next page if current page is not the last page
    Break the loopat the last page
    """

    # Get category URL, i.e., the link to the first page of books under category
    books_page_url = base_url_for_category + category.find("a").get("href")

    # Scrape books page by page only when the next page is available
    while True:
        # Retrieve the products list page's HTML
        get_current_page = requests.get(books_page_url)

        # Create BeautifulSoup object for current page
        current_page_soup = soup(get_current_page.text, "html.parser")

        # Run fetch_current_page_books() function to get all the products listed
        # on current page
        fetch_current_page_books(category_name, current_page_soup)

        # Search for next page's URL
        try:
            # Get the next page's URL if the current page is not the last
            find_next_page_url = current_page_soup.find("li", {"class": "next"}).find("a").get("href")

            # Find the index of the last '/'
            idx = books_page_url.rfind("/")

            # Skip the string after the last '/' and add the next page URL
            books_page_url = books_page_url[:idx+1].strip() + find_next_page_url

        except:
            # If last page, break out of loop
            break


def fetch_current_page_books(category_name, current_page_soup):
    """
    Fetch all the books listed on current page.
    Build a dictionary to store the extracted data.
    Append book information to the books_all list
    """
    # Find all products listed on the current page
    # Here we don't need to identify the class name of <li>
    current_page_books = current_page_soup.find("ol", {"class": "row"}).find_all("li")

    # Loop through each product
    for book in current_page_books:
        # Extract book info of interest

        # Get book title
        title = book.find("h3").find("a").get("title").strip()

        # Get book price
        price = book.find("p", {"class": "price_color"}).text.strip()

        # Get in stock info
        instock = book.find("p", {"class": "instock availability"}).text.strip()

        # Get rating
        # We will get a list, ['star-rating', 'Two'], by using get('class') only,
        # so here, we slice the list to extract rating only
        rating_in_words = book.find("p").get("class")[1]
        rating = w_to_d[rating_in_words]

        # Get link
        link = book.find("h3").find("a").get("href").strip()
        link = base_url_for_book + link.replace("../../../", "")

        # Get more info about book by running fetch_more_info() function
        product_info = fetch_more_info(link)

        # Create a book dictionary to store the book's info
        book = {
            "scraping_date": scraping_date,
            "book_title": title,
            "category": category_name,
            "price": price,
            "rating": rating,
            "instock": instock,
            "availability": product_info["Availability"],
            "UPC": product_info["UPC"],
            "link": link,
        }

        # Append book dictionary to books_all list
        books_all.append(book)


def fetch_more_info(link):
    """
    Go to a single product page to get more info
    """
    # Get URL of the web page
    get_url = requests.get(link)
    
    # Create BeautifulSoup object for the book
    book_soup = soup(get_url.text, "html.parser")

    # Find the product information table
    book_table = book_soup.find("table", {"class": "table table-striped"}).find_all("tr")

    # Build a dictionary to store the information in the table
    product_info = {}

    # Loop through the table
    for info in book_table:
        # Use header cells as key
        key = info.find("th").text.strip()

        # Use cells as values
        value = info.find("td").text.strip()

        # Update dictionary
        product_info[key] = value
    
    # Extract number from availability using Regex and update value in dict
    text = product_info["Availability"]
    product_info["Availability"] = re.findall(r"(\d+)", text)[0]

    # Return dictionary with product info
    return product_info


def fetch_all_books(soup_object):
    """
    Fetch all the books information
    Return:
    - books_all, a list of dictionaries that contains all the
      extracted data
    """
    # Find all the categories by running find_categories() function
    categories = find_categories(soup_object)

    # Loop through each category
    # for category in categories[:4]:   # If you want to scrape a few pages
    for category in categories:         # Get full web page
        # Fetch product by category
        category_name = category.find("a").text.strip()

        # Within the fetch_books_by_category() function, we will scrape
        # products page by page
        fetch_books_by_category(category_name, category)

    return books_all


def output(books_list):
    """
    Convert the list with scraped data to a DataFrame, drop the duplicates,
    and save the output as a CSV file
    """
    # Convert the list to a DataFrame, drop the duplicates
    book_df = pd.DataFrame(books_list).drop_duplicates()
    print(f"There are in total {len(book_df)} books.")

    # Print DataFrame
    # print(book_df)

    # Save the output to a CSV file
    book_df.to_csv(f"book_scraper_{scraping_date}.csv", index=False)


# -----------------------------------
# Run 'main' function:
# -----------------------------------
if __name__ == "__main__":
    main()