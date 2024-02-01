import tkinter as tk
from tkinter import ttk
from bs4 import BeautifulSoup
import requests
import webbrowser
import re
import customtkinter as ctk
from CTkTable import *
from custom_hovertip import CustomTooltipLabel as ctt
from datetime import datetime  # Import the datetime module
import lxml
import cchardet
from functools import partial

# Define the list of stores and their URLs
store_urls = [
    ('BOOKSAMILLION', 'https://www.booksamillion.com/search?query='),
    ('GameStop', 'https://www.gamestop.com/search/?q='),
    ('Kohl\'s', 'https://www.kohls.com/search.jsp?submit-search=web-regular&search='),
    ('Macy\'s', 'https://www.macys.com/shop/featured/'),
    ('Monoprice', 'https://www.monoprice.com/search/index?keyword='),
    ('Newegg', 'https://www.newegg.com/p/pl?d='),
    ('Office Depot', 'https://www.officedepot.com/a/search/?q='),
    ('Zulily', 'https://www.zulily.com/search?q=')
    # Add more store URLs here
]

# Create a dictionary to store the store names and their corresponding prices and URLs
prices = {}
bookmarked_items = []

# Create a dictionary to store the store names and their corresponding prices and URLs
def fetch_prices(upc, store_checkboxes, sort_by_price=False, sort_by_rating=False, sort_by_alphabet=False):
    selected_stores = [store for store, var in store_checkboxes.items() if var.get() == 1]

    # Create a dictionary to store the store names and their corresponding prices and ratings
    prices = {}

    for store_name, store_url in store_urls:
        if store_name in selected_stores:
            try:
                url = store_url + upc

                # *******************************************************************
                #if store_name == 'Gamestop':
                    #url = store_url + upc + '&lang=default&start=0&sz=20'
                    #continue
                # Trying to add the rest of the URL to the end of the Gamestop UPCs
                # But this does not seem to work
                # *******************************************************************

                headers = {
                    'User-Agent': 'Your User Agent Here',
                }

                response = requests.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'lxml')

                # Initialize price and rating with default values
                price = "Price not found"
                rating = "--"

                # Extract the price and rating (modify according to store HTML structure)
                if store_name == 'BOOKSAMILLION':
                    price_html = soup.find('span', {'class': 'our-price'})
                    rating_html = soup.find('div', {'class': 'pr-snippet-rating-decimal'})
                if store_name == 'GameStop':
                    price_html = soup.find('div', {'class': 'render-sale-price'})
                    rating_html = soup.find('div', {'class': 'red-stars star-img'})
                if store_name == 'Kohl\'s':
                    price_html = soup.find('ul', {'class': 'pricingList'})
                    rating_html = soup.find('div', {'class': 'bv_avgRating_component_container notranslate'})
                if store_name == 'Macy\'s':
                    price_html = soup.find('div', {'class': 'lowest-sale-price'})
                    rating_html = soup.find('div', {'class': 'show-for-sr'})
                if store_name == 'Monoprice':
                    price_html = soup.find('p', {'class': 'hawk-itemPrice'})
                    rating_html = soup.find('div', {'class': 'hawk-listingRating'})
                if store_name == 'Newegg':
                    price_html = soup.find('li', {'class': 'price-current'})
                    rating_html = soup.find('div', {'class': 'rating'})
                if store_name == 'Office Depot':
                    price_html = soup.find('span', {'class': 'od-graphql-price-big-price'})
                    rating_html = soup.find('div', {'class': 'od-stars-inner'})
                if store_name == 'Zulily':
                    price_html = soup.find('div', {'class': 'product-item__price'})
                    rating_html = soup.find('div', {'class': 'rating'})
                print(price_html)
                print(rating_html)
                # Add more store-specific code for other websites here

                # Update price and rating if found on the website
                if price_html:
                    # Use regular expressions to clean and format the price
                    price_text = re.search(r'\$\d+\.\d{2}', price_html.get_text())
                    if price_text:
                        price = price_text.group()

                if price != "Price not found":
                    if rating_html:
                        # Extract the rating from the found HTML element
                        if store_name == 'Office Depot':
                            rating_match = re.search(r'width:\s*(\d+)%', rating_html['style'])
                        #if store_name == 'Gamestop':
                            #rating_match = re.search(r'width:\s*(\d+)%', rating_html['style'])
                        else:
                            rating_text = rating_html.get_text()
                            rating_match = re.search(r'(\d+(\.\d+)?)%', rating_text)
                        # rating_match = re.search(r'\d+', rating_text)

                        # *********************************************************************
                        # ^ Will not extract the number from text like: "<div class="od-stars-inner" style="width:80%"></div>"
                        # May need a hand figuring that out. ^
                        # *********************************************************************

                        if rating_match:
                            rating = rating_match.group(1)
                        else:
                            rating = "--"
                    else:
                        rating = "--"
                    print(rating)

                    prices[store_name] = {'price': price, 'rating': rating, 'url': url}

            except Exception as e:
                print(f"Error fetching data from {url}: {str(e)}")

    # Sort results based on sorting options
    if sort_by_price:
        prices = dict(sorted(prices.items(), key=lambda x: float(x[1]['price'].strip('$')) if re.match(r'\$\d+\.\d{2}',x[1]['price']) else float('inf')))
    elif sort_by_rating:
        prices = dict(sorted(prices.items(),key=lambda x: float(re.search(r'(\d+(\.\d+)?\s*%)', x[1]['rating']).group(1)) if re.search(r'(\d+(\.\d+)?\s*%)', x[1]['rating']) else 0, reverse=True))
    elif sort_by_alphabet:
        prices = dict(sorted(prices.items()))

    return prices


def search_product():
    upc = upc_entry.get()

    # Check the length of the UPC
    if len(upc) != 12:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Invalid UPC", "UPC must be 12 digits!")
        return  # Exit the function or event handler early

    if upc:
        selected_option = sorting_option.get()
        if selected_option == "price":
            sort_by_price = True
            sort_by_rating = False
            sort_by_alphabet = False
        elif selected_option == "rating":
            sort_by_price = False
            sort_by_rating = True
            sort_by_alphabet = False
        elif selected_option == "alphabet":
            sort_by_price = False
            sort_by_rating = False
            sort_by_alphabet = True
        else:
            sort_by_price = False
            sort_by_rating = False
            sort_by_alphabet = False

        prices = fetch_prices(upc, store_checkboxes, sort_by_price, sort_by_rating, sort_by_alphabet)

        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)

        if not prices:
            result_text.insert(tk.END, "No results found")
        else:
            lowest_price = float('inf')
            highest_rating = 0  # Initialize highest rating

            for store, data in prices.items():
                result_text.insert(
                    tk.END, f'{store}: {data["price"]} | {data["rating"]}% | '
                )

                # Identify the lowest price and the highest rating
                price_value = float(data["price"].strip('$'))
                if price_value < lowest_price:
                    lowest_price = price_value

                rating_text = data["rating"]
                if rating_text != '--':
                    rating_value = float(rating_text)
                    if rating_value > highest_rating:
                        highest_rating = rating_value

                # Display the URL as a hyperlink
                result_text.insert(tk.END, '\n')
                hyperlink_label = tk.Label(result_text, text=data["url"], fg="blue", cursor="hand2")
                hyperlink_label.bind("<Button-1>", lambda e, url=data["url"]: open_url(e, url))
                result_text.window_create(tk.END, window=hyperlink_label)

                # Add the "bookmark" button
                result_text.insert(tk.END, '\n')
                bookmark_button = tk.Button(result_text, text="Bookmark", command=partial(bookmark_item, store, data),
                                            cursor="hand2")
                result_text.window_create(tk.END, window=bookmark_button)
                result_text.insert(tk.END, '\n')
                result_text.insert(tk.END, '\n')

            # Apply bold font to the lowest price and the highest rating
            for store, data in prices.items():
                if float(data["price"].strip('$')) == lowest_price:
                    start = result_text.search(f'{data["price"]}', 1.0, tk.END)
                    if start:
                        end = start + f"+{len(data['price'])}c"
                        result_text.tag_add("bold", start, end)
                        result_text.tag_configure("bold", font=('Arial', 10, 'bold'))

                if data["rating"] != '--' and float(data["rating"]) == highest_rating:
                    # Locate the rating in the text
                    start = result_text.search(f'{data["rating"]}', 1.0, tk.END)
                    if start:
                        end = start + f"+{len(data['rating'])}c"
                        result_text.tag_add("bold", start, end)
                        result_text.tag_configure("bold", font=('Arial', 10, 'bold'))

                        # Add the percentage symbol and make it bold
                        percentage_start = result_text.search('%', end)
                        if percentage_start:
                            percentage_end = percentage_start + "+1c"
                            result_text.tag_add("bold", start,
                                                percentage_end)  # Update this line to include the rating number
                            result_text.tag_configure("bold", font=('Arial', 10, 'bold'))

        result_text.config(state=tk.DISABLED)

        update_history()


# Update the history table
def update_history():
    global historyRow
    upc = upc_entry.get()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current date and time
    historyTable.insert("", "end", values=(upc, date))  # Insert both UPC and date
    historyRow += 1

# Double-click event handler for the history table
def on_history_item_single_click(event):
    item = historyTable.identify_row(event.y)  # Get the item that was clicked
    if item:
        upc = historyTable.item(item, "values")[0]  # Get the UPC value from the selected item
        upc_entry.delete(0, "end")  # Clear the current UPC entry
        upc_entry.insert(0, upc)  # Populate the UPC entry with the selected UPC

def bookmark_item(store, data):
    global bookmarked_items
    # Check if the item is already bookmarked
    if not any(item['store'] == store and item['data']['url'] == data['url'] for item in bookmarked_items):
        bookmarked_items.append({'store': store, 'data': data})
        update_bookmarks_tab()


def update_bookmarks_tab():
    bookmarks_text.config(state=tk.NORMAL)
    bookmarks_text.delete(1.0, tk.END)

    for item in bookmarked_items:
        store_name = item["store"]
        data = item["data"]
        bookmarks_text.insert(tk.END, f'{store_name}: {data["price"]} | {data["rating"]}% | ')

        # Create a hyperlink as a Label widget for the bookmarked URL
        hyperlink_label = tk.Label(bookmarks_text, text=data["url"], fg="blue", cursor="hand2")
        hyperlink_label.bind("<Button-1>", lambda event, url=data["url"]: open_url(event, url))
        bookmarks_text.window_create(tk.END, window=hyperlink_label)
        bookmarks_text.insert(tk.END, '\n')

        remove_button = tk.Button(bookmarks_text, text="Remove", command=partial(remove_bookmark, store_name, data),
                                  cursor="hand2")
        bookmarks_text.window_create(tk.END, window=remove_button)
        bookmarks_text.insert(tk.END, '\n')
        bookmarks_text.insert(tk.END, '\n')

    bookmarks_text.config(state=tk.DISABLED)



def open_url(event, url):
    webbrowser.open(url)

def remove_bookmark(store, data):
    global bookmarked_items
    # Search for the item in the bookmarked items list and remove it
    bookmarked_items = [item for item in bookmarked_items if not (item['store'] == store and item['data'] == data)]
    # Refresh the bookmarks tab
    update_bookmarks_tab()


def select_all():
    for store_name in store_checkboxes:
        store_checkboxes[store_name].set(1)


def deselect_all():
    for store_name in store_checkboxes:
        store_checkboxes[store_name].set(0)


def apply_and_search():
    search_product()

def main():
    # Create the main window
    root = tk.Tk()
    root.title("Cluepon")
    root.geometry("600x600")

    # Title Label
    ctk.CTkLabel(root, text="Cluepon", font=('Arial', 20, 'bold')).pack(pady=(10, 0))

    # Create the CTkTabview (tabs)
    global tabview
    tabview = ctk.CTkTabview(master=root)
    tabview.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

    # Tabs
    tab1 = tabview.add("Search")
    tab2 = tabview.add("Filters")
    tab3 = tabview.add("Bookmarks")
    tab4 = tabview.add("History")
    tab5 = tabview.add("Help")

    # Search Tab (tab1)--------------------------------------------------------------------------------------
    # Title Label
    ctk.CTkLabel(tab1, text="Search for the best price and rating on your favorite items.").pack(pady=5)

    # UPC Entry
    upc_label = ctk.CTkLabel(tab1, text="Enter UPC Code:")
    upc_label.pack(pady=2)

    global upc_entry
    upc_entry = ctk.CTkEntry(tab1)
    upc_entry.pack(pady=3, ipadx=10, ipady=5)

    # Search Button
    search_button = ctk.CTkButton(tab1, text="Search", command=search_product)
    search_button.pack(pady=5)

    # Results Text Widget
    global result_text
    result_text = tk.Text(tab1, wrap=tk.WORD, height=30, width=70)
    result_text.pack(pady=5, padx=20)
    result_text.config(state=tk.DISABLED)

    # Hyperlink configurations
    result_text.tag_config("hyperlink", foreground="blue", underline=True)
    result_text.tag_bind("hyperlink", "<Enter>", lambda e: result_text.config(cursor="hand2"))
    result_text.tag_bind("hyperlink", "<Leave>", lambda e: result_text.config(cursor="arrow"))

    # Filtering Tab (tab2)--------------------------------------------------------------------------------------
    global sorting_option
    sorting_option = tk.StringVar()  # Create a variable to hold the selected sorting option
    sorting_option.set("price")  # Price is selected by default

    # Create Radio buttons for sorting options
    sort_by_price_button = ctk.CTkRadioButton(tab2, text="Sort by Best Price", variable=sorting_option, value="price")
    sort_by_price_button.pack(pady=5)
    ctt(anchor_widget=sort_by_price_button, text="Sort by best price ascending")
    sort_by_rating_button = ctk.CTkRadioButton(tab2, text="Sort by Rating", variable=sorting_option, value="rating")
    sort_by_rating_button.pack(pady=5)
    ctt(anchor_widget=sort_by_rating_button, text="Sort by best rating ascending")
    sort_by_alphabet_button = ctk.CTkRadioButton(tab2, text="Sort by Alphabet", variable=sorting_option,
                                                 value="alphabet")
    sort_by_alphabet_button.pack(pady=5)
    ctt(anchor_widget=sort_by_alphabet_button, text="Sort by ascending alphabetical order")

     # Create "Select All" button
    select_all_button = ctk.CTkButton(tab2, text="Select All", command=select_all)
    select_all_button.pack(pady=5)
    ctt(anchor_widget=select_all_button, text="Select all stores")

    # Create "Deselect All" button
    deselect_all_button = ctk.CTkButton(tab2, text="Deselect All", command=deselect_all)
    deselect_all_button.pack(pady=5)
    ctt(anchor_widget=deselect_all_button, text="Deselect all stores")

    # Create Check boxes for store selection
    global store_checkboxes
    store_checkboxes = {}  # Dictionary of store names to make checkboxes
    for store_name, _ in store_urls:
        store_checkboxes[store_name] = tk.IntVar(value=1)  # Set the value to 1 to select by default
        store_checkbutton = ctk.CTkCheckBox(tab2, text=store_name, variable=store_checkboxes[store_name])
        store_checkbutton.pack(pady=5)

    # Create "Apply and Search" button
    apply_search_button = ctk.CTkButton(tab2, text="Apply and Search", command=apply_and_search)
    apply_search_button.pack(pady=10)
    ctt(anchor_widget=apply_search_button, text="Apply filter settings")

    # Bookmarks Tab (tab3)--------------------------------------------------------------------------------------
    global bookmarks_text
    bookmarks_text = tk.Text(tab3, wrap=tk.WORD, height=30, width=70)
    bookmarks_text.pack(pady=20, padx=20)
    bookmarks_text.config(state=tk.DISABLED)


    # History Tab (tab4)----------------------------------------------------------------------------------------

    # Title Label
    ctk.CTkLabel(tab4, text="Recent Searches").pack(pady=20)
    ctk.CTkLabel(tab4, text="(Click to select a UPC to search for.)").pack(pady=2)

    # History Table
    value = [[],
             []]

    global historyTable
    historyTable = ttk.Treeview(tab4, columns=("UPC", "Date"), show="headings")
    historyTable.heading("UPC", text="UPC")
    historyTable.heading("Date", text="Date")
    historyTable.column("UPC", width=100)
    historyTable.column("Date", width=100)
    historyTable.pack(expand=True, fill="both", padx=20, pady=20)
    historyTable.bind("<Button-1>", on_history_item_single_click)  # Bind double-click event

    global historyRow
    historyRow = 0

    # Search Button
    search_button = ctk.CTkButton(tab4, text="Search", command=search_product)
    search_button.pack(pady=20)

    # Help Tab (tab5)-------------------------------------------------------------------------------------------
    ctk.CTkLabel(tab5, text="Cluepon User Manual").pack(pady=10)

    ctk.CTkLabel(tab5, text="Search Tab")

    # Use the pack method to make the Text widget expand with the frame
    textbox = ctk.CTkTextbox(tab5, height=20, width=50, wrap="word")
    textbox.pack(expand=True, fill="both", padx=20, pady=10)

    textbox.insert("0.0",
        "\n\nThis is where previous UPC searches are stored."
        "\n\nIf you wish to repeat a previous search, click on the desired entry and press the \"Search\" button. You may then switch to the SEARCH TAB to view the results."
        "\n\n")
    textbox.insert("0.0",
        "\n\n\nHISTORY TAB")
    textbox.insert("0.0",
        "\n\nThis is where bookmarked items from the SEARCH TAB are stored."
        "\n\nIf you have bookmarks saved, you can view their item information and click on their links to navigate to their respective item pages on a web browser, just as you can with search results."
        "\n\nTo remove a bookmark, click the \"Remove\" button below the bookmarked item you wish to delete.")
    textbox.insert("0.0",
        "\n\n\nBOOKMARKS TAB")
    textbox.insert("0.0",
        "\n\nThis is where you can choose how to order your search results as well as which stores to search through."
        "\n\nTo order your search results by alphabetical order, best price, or best rating, select the radio button of your preferred sorting method near the top of the tab window."
        "\n\nBelow the sorting options you will find the list of currently-selected stores. You will find options to select all, deselect all, or manually select stores by clicking the checkboxes next to them."
        "\n\nOnce all sorting and filtering options are set up, you may click the \"Apply and Search\" button to conduct the search. You may then switch to the SEARCH TAB to view the results."
        "\n\nThe list of currently supported stores is as follows:"
        "\n\n  GameStop\n  Khol\'s\n  Macy\'s\n  Newegg\n  Office Depot\n  Monoprice\n  Zulily")
    textbox.insert("0.0",
        "\n\n\nFILTERS TAB")
    textbox.insert("0.0",
        "\n\nThis is where you can perform searches for items across various online stores (see further below for a full list.)"
        "\n\nTo perform a search enter a Universal Product Code (UPC) or a link to your desired into the search bar and press the \"Search\" button."
        "\n\nAfter the search results load, a list of stores selling the item you want will be displayed. Each store's price and rating for the item will also be displayed. If you find a result you like, you may click the provided link to be taken to your product's page."
        "\n\nYou may also bookmark search results for future reference by ticking the checkbox next to the desired results and clicking the \"Save bookmarked results\" button.")
    textbox.insert("0.0",
                   "SEARCH TAB")
    textbox.configure(state="disabled")  # configure textbox to be read-only

    root.mainloop()


if __name__ == "__main__":
    main()
