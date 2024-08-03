import os
import io
import sqlite3
from colorama import Fore, Back, Style
from playsound import playsound
from progress.bar import ChargingBar
import qrcode
import argparse
import json
import shutil

# Argument Parsing
option = False
parser = argparse.ArgumentParser("python3 ims.py")
parser.add_argument('-o', '--option', dest="option", type=str, help="Skip menu and perform a preset action")
parser.add_argument('-r', '--rapidScan', help="Enable to scan repeatedly and skip menu", action='store_true')
arg = parser.parse_args()

onStart = True
quitAfter = False # Ends program

b = '\033[1m' # Bold
u = '\033[4m' # Underline
e = '\033[0m' # End

# qr_add_one = qrcode.QRCode(border=1)
# qr_add_one.add_data('add-one')
# f = io.StringIO()
# qr_add_one.print_ascii(out=f)
# f.seek(0)

def mainMenuOptions():
  print("a) Add Stock +1")
  print("m) Minus Stock -1")
  print("n) New Inventory Item")
  print("f) Find Item")
  print("p) Print Reorder List")
  print("s) Settings")
  print("q) Quit")

splash = """
 _               _                
(_)___  __ _  __| | ___  _ __ ___ 
| / __|/ _` |/ _` |/ _ \| '__/ _ \ 
| \__ \ (_| | (_| | (_) | | |  __/
|_|___/\__,_|\__,_|\___/|_|  \___|"""

appVersion = "v0.0.1"

# Functions
def clear():
  os.system('cls' if os.name == 'nt' else 'clear')

def sleep(seconds):
  os.system('sleep ' + str(seconds))

def create_sqlite_database(filename):
  """ create a database connection to an SQLite database """
  conn = None
  try:
    conn = sqlite3.connect(filename)
    print(sqlite3.sqlite_version)
  except sqlite3.Error as e:
    print(e)
  finally:
    if conn:
      conn.close()

def create_tables():
  sql_statements = [
    """CREATE TABLE IF NOT EXISTS items (
      item_id INTEGER NOT NULL PRIMARY KEY,
      item_name text NOT NULL,
      item_code text,
      item_productcode text,
      item_stock int,
      item_reorder int,
      item_link text,
      item_img text,
      item_status text
    );"""
  ]
  try:
    with sqlite3.connect('src/isadore.db') as conn:
      cursor = conn.cursor()
      for statement in sql_statements:
        cursor.execute(statement)
      conn.commit()
      print(conn)
  except sqlite3.Error as e:
    print(e)

# Status colors
colors = {
  "Active": Fore.GREEN,
  "Inactive": Style.DIM,
  "Reorder": Fore.YELLOW,
  "Out of Stock": Fore.RED
}

def add_item(data):
  
  if (data[1] is None or data[1] == ""):
    data[1] = None
  if (data[2] is None or data[2] == ""):
    data[2] = None
  if (data[3] is None or data[3] == ""):
    data[3] = 0
  # If no reorder quantity
  if (data[4] is None or data[4] == ""):
    data[4] = 0
  try:
    with sqlite3.connect('src/isadore.db') as conn:
      cur = conn.cursor()
      cur.execute('INSERT INTO items(item_name, item_code, item_productcode, item_stock, item_reorder, item_status) VALUES(?,?,?,?,?,"Active")', (data))
      conn.commit()
      return cur.lastrowid
  except sqlite3.Error as e:
    print(e)
    return 0

def lookup_item(userInput):
  if (userInput == "q"):
    return userInput # and go to main menu
  else:
    try:
      with sqlite3.connect('src/isadore.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT item_id, item_name, item_stock FROM items WHERE item_code = ? OR item_productcode = ? OR item_name LIKE ? LIMIT 1', (userInput,userInput,'%'+userInput+'%'))
        conn.commit()
        result = cur.fetchone()
        if (result is not None):
          return result
        else:
          return 0
    except sqlite3.Error as e:
      return 0

def get_item_data(userInput):
  try:
    with sqlite3.connect('src/isadore.db') as conn:
      cur = conn.cursor()
      cur.execute('SELECT * FROM items WHERE item_id = ?', (userInput,))
      conn.commit()
      result = cur.fetchone()
      if (result is not None):
        return result
      else:
        return 0
  except sqlite3.Error as e:
    return 0

def update_item_field(field, data, itemId):
  try:
    with sqlite3.connect('src/isadore.db') as conn:
      cur = conn.cursor()
      cur.execute('UPDATE items SET ' + field + ' = ? WHERE item_id = ?', (data, itemId,))
      conn.commit()
      return True
  except:
    return 0

def add_one(item_id):
  try:
    with sqlite3.connect('src/isadore.db') as conn:
      cur = conn.cursor()
      cur.execute('UPDATE items SET item_stock = item_stock + 1 WHERE item_id = ?', (item_id,))
      conn.commit()
      return True
  except sqlite3.Error as e:
    return 0

def minus_one(item_id):
  try:
    with sqlite3.connect('src/isadore.db') as conn:
      cur = conn.cursor()
      cur.execute('UPDATE items SET item_stock = item_stock - 1 WHERE item_id = ?', (item_id,))
      conn.commit()
      return True
  except sqlite3.Error as e:
    return 0

def delete_item(code):
  try:
    with sqlite3.connect('src/isadore.db') as conn:
      cur = conn.cursor()
      cur.execute('DELETE FROM items WHERE item_code = ?', (code,))
      conn.commit()
      return True
  except sqlite3.Error as e:
    return 0

# Setup Database
create_sqlite_database("src/isadore.db")
create_tables()


# Main Program Loop
mainMenuUnrec = False
rapidScanSuccess = False
while True:
  clear()
  print(Fore.MAGENTA + splash)
  print(Fore.GREEN + " Inventory Management      " + Fore.LIGHTBLUE_EX + "%s\n" % appVersion)
  print(Fore.RESET + "MAIN MENU\n")
  mainMenuOptions()
  if (mainMenuUnrec == True):
    print(Fore.RED + "\nUnrecognized command. Please try again." + Fore.RESET)
    mainMenuUnrec = False
    
  # If no arguments
  if (arg.option is None or arg.option == False):
    option = input("\nEnter option: ").lower()
  else:
    onStart = False
    option = arg.option
    quitAfter = True

  goback = Style.DIM + 'Press "q" to go back' + Style.RESET_ALL + "\n"

  # Add 1 item
  if (option == 'add-one' or option == "a"):
    clear()
    print("┌───────────────┐")
    print("│ ADD STOCK ONE │")
    print("└───────────────┘")
    print(goback)
    if (rapidScanSuccess == True):
      print(Fore.GREEN + "Success" + Fore.RESET)
      rapidScanSuccess = False
    barcode = input(Style.RESET_ALL + "Scan item barcode: ")
    
    print(f"Looking up item with barcode: {barcode}")
    item_data = lookup_item(barcode)
    if (item_data != 0):
      if (item_data != "q"): # quit and go back
        print("Found item: " + Fore.GREEN + item_data[1] + Fore.RESET)
        print(f"Current stock: {item_data[2]}")
        print("Updating quantity +1")
        update = add_one(item_data[0])
        if (update is not None):
          print(Fore.GREEN + "Success!" + Fore.RESET)
          new_data = lookup_item(barcode)
          print(f'Adjusted stock for "{new_data[1]}": {new_data[2]}')
          if (arg.rapidScan is not None and arg.rapidScan == True):
            rapidScanSuccess = True
        else:
          print(Fore.RED + "Error: Failed to update database" + Fore.RESET)
    else:
      print(Fore.RED + "Error: No item found with that barcode" + Fore.RESET)
      sleep(1)

    if (arg.rapidScan is None or arg.rapidScan == False):
      if (item_data != "q"):
        if (quitAfter is None or arg.rapidScan == False):
          sleep(2)
      if (quitAfter == True):
        clear()
        exit()
    else:
      arg.option = 'add-one'
    clear()

  # Minus 1 item
  elif (option == 'minus-one' or option == "m"):
    clear()
    print("┌─────────────────┐")
    print("│ MINUS STOCK ONE │")
    print("└─────────────────┘")
    print(goback)
    barcode = input(Style.RESET_ALL + "Scan item barcode: ")
    print(f"Looking up item with barcode: {barcode}")
    item_data = lookup_item(barcode)
    if (item_data != 0):
      if (item_data != "q"): # quit and go back
        print("Found item: " + Fore.BLUE + item_data[1] + Fore.RESET)
        print(f"Current stock: {item_data[2]}")
        print("Updating quantity -1")
        update = minus_one(item_data[0])
        if (update is not None):
          print(Fore.BLUE + "Done" + Fore.RESET)
          new_data = lookup_item(barcode)
          print(f'Adjusted stock for "{new_data[1]}": {new_data[2]}')
        else:
          print(Fore.RED + "Error: Failed to update database" + Fore.RESET)
    else:
      print(Fore.RED + "Error: No item found with that barcode" + Fore.RESET)

    if (arg.rapidScan is None or arg.rapidScan == False):
      if (item_data != "q"):
        sleep(2)
      if (quitAfter == True):
        clear()
        exit()
    clear()

  # Find Existing Inventory Item
  elif (option == 'find' or option == "f"):
    clear()
    inputEmpty = False
    inputError = False
    while True:
      clear()
      print("┌───────────┐")
      print("│ FIND ITEM │")
      print("└───────────┘")
      print(goback)
      if (inputEmpty):
        print(Fore.RED + "Error: No input received. Try again." + Fore.RESET)
      if (inputError):
        print(Fore.RED + "Error: Could not find item using that information." + Fore.RESET)
      userInput = input("Enter item name, product code, or scan barcode to look up item: ")
      if (userInput == '' or userInput is None):
        inputEmpty = True
      else:
        if (userInput == 'q'):
          break
        itemData = lookup_item(userInput)
        if (itemData != 0):
          clear()
          print(f'Found item: "{itemData[1]}"')
          confirmInvalid = True
          while (confirmInvalid):
            confirm = input("Is this correct? (Y/n): ")
            if (confirm == 'y' or confirm == 'n'):
              confirmInvalid = False
              if (confirm == 'y'):
                clear()
                # Print Item Data
                itemData = get_item_data(itemData[0])
                print(f'Name:                 {itemData[1]}')
                print(Style.DIM + 'ID:                   ' + str(itemData[0]) + Style.RESET_ALL)
                print(f'Product Code/ID:      {itemData[3]}')
                print(f'Barcode:              {itemData[2]}')
                if (itemData[4] <= itemData[5]):
                  quantity = Fore.RED + b + str(itemData[4]) + e + Fore.RESET
                else:
                  quantity = itemData[4]
                print(f'Current Stock:        {quantity}')
                print(f'Quantity to Reorder:  {itemData[5]}')
                print('Status:               ' + colors[itemData[8]] + itemData[8] + Fore.RESET)
                optionInvalid = True
                while (optionInvalid):
                  print("\n['q' = Go Back]  ['u' = Update Quantity]  ['e' = Edit Item]")
                  option = input('\nSelect option: ')
                  if (option == 'e'):
                    clear()
                    print(Fore.YELLOW + 'Editing Item: "' + itemData[1] + '"\n' + Fore.RESET)
                    print('n) Name:             ' + itemData[1])
                    print('p) Product Code:     ' + itemData[3])
                    print('b) New Barcode:      ' + itemData[2])
                    print('c) Current Stock:    ' + str(itemData[4]))
                    print('r) Reorder Quantity: ' + str(itemData[5]))
                    print('s) Status:           ' + colors[itemData[8]] + itemData[8] + Fore.RESET)
                    print('\nq) Go Back\n')
                    editOption = input('Select option: ')
                    if (editOption == 'n'):
                      index = 1
                      editOption = 'Name'
                      field = 'item_name'
                    elif (editOption == 'p'):
                      index = 3
                      editOption = 'Product Code'
                      field = 'item_productcode'
                    elif (editOption == 'b'):
                      index = 2
                      editOption = 'Barcode'
                      field = 'item_code'
                    elif (editOption == 'c'):
                      index = 4
                      editOption = 'Current Stock'
                      field = 'item_stock'
                    elif (editOption == 'r'):
                      index = 5
                      editOption = 'Reorder Quantity'
                      field = 'item_reorder'
                    elif (editOption == 's'):
                      index = 8
                      editOption = 'Status'
                      field = 'item_status'
                    clear()
                    print(Fore.YELLOW + 'Chaning ' + editOption + Fore.RESET)
                    print(Style.DIM + 'Old ' + editOption + ': ' + itemData[index] + Style.RESET_ALL)
                    newData = input(f'\nEnter new {editOption}: ')
                    if (newData != ''):
                      didUpdate = update_item_field(field, newData, itemData[0])
                      if (didUpdate != 0):
                        clear()
                        print(Fore.GREEN + 'Successfully updated item!' + Fore.RESET)
                        input('Press enter to go back.')
                      else:
                        clear()
                        print(Fore.RED + 'Error: Could not update item' + Fore.RESET)
                        input('Press enter to go back.')
                    break
                  elif (option == 'u'):
                    inputError = True
                    while (inputError == True):
                      clear()
                      print('Updating Quantity for "' + itemData[1] + '"')
                      print(Fore.CYAN + 'Hint: Use minus symbol to subtract from current stock.' + Fore.RESET)
                      addSubtract = input('\nAmount to add/subtract: ')
                      print(addSubtract)
                      if (isinstance(int(addSubtract), int)):
                        print("Good")
                        input("Enter to go back")
                        inputError = False
                      else:
                        print(Fore.RED + "Invalid input" + Fore.RESET)
                        input("Press Enter")
                    break
                  elif (option == 'q'):
                    optionInvalid = False
                    break
            else:
              confirmInvalid = True
        else:
          inputError = True


  # Create New Inventory Item
  elif (option == 'new-item' or option == "n"):
    clear()
    print("┌────────────────────┐")
    print("│ NEW INVENTORY ITEM │")
    print("└────────────────────┘")
    print(goback)
    print(Fore.RED + "*" + Fore.RESET + Style.DIM + " Required" + Style.RESET_ALL)
    item = []
    noInput = False
    firstPrompt = True
    duplicateBarcode = False
    while (noInput == True or firstPrompt == True):
      firstPrompt = False
      item_data = input("Item name: " + Fore.RED + "*" + Fore.RESET + " ")
      if (item_data == "" or item_data is None):
        print(Fore.RED + "Item name is required." + Fore.RESET)
        noInput = True
        firstPrompt = True
      else:
        noInput = False # continue
    item.append(item_data)
    firstPrompt = True
    while (duplicateBarcode == True or firstPrompt == True):
      firstPrompt = False
      item_data = input("Enter/scan barcode: ")
      check_barcode = lookup_item(item_data)
      if (check_barcode != 0):
        print(Fore.RED + 'Item "' + check_barcode[1] + '" has duplicate barcode. Try again.' + Fore.RESET)
        duplicateBarcode = True

    item.append(item_data)
    item_data = input("Product code: ")
    item.append(item_data)
    item_data = input("Opening stock: ")
    item.append(item_data)
    item_data = input("Reorder quantity: ")
    item.append(item_data)
    new_itemId = add_item(item)
    if (new_itemId == 0):
      print(Fore.RED + "Error: Failed to create item in database." + Fore.RESET)
      input("Press 'enter' to finish.")
    else:
      print(Fore.GREEN + "\nSuccessfully created item!" + Fore.RESET)
      if (quitAfter == True):
        clear()
        exit()
      else:
        input("Press 'enter' to finish.")

  # Isadore Settings
  elif (option == 'settings' or option == "s"):
    quitSettings = False
    noInput = False
    invalidInput = False
    while (quitSettings == False):
      clear()
      print(Fore.MAGENTA + splash + Fore.RESET)
      print("┌──────────┐")
      print("│ SETTINGS │")
      print("└──────────┘")
      print(goback)
      print("Options:\n")
      print("i)  Import Existing Database File")
      print("e)  Export Database File")
      if (noInput):
        print(Fore.RED + "Error: No input provided." + Fore.RESET)
      if (invalidInput):
        print(Fore.RED + "Error: Not a valid option." + Fore.RESET)
      settingsOption = input("\nEnter an option: ")
      if (settingsOption == '' or settingsOption is None):
        noInput = True
      else:
        noInput = False
        if (settingsOption == 'i'):
          clear()
          print(Fore.YELLOW + "Import Existing Database File" + Fore.RESET)
          print("Enter the full path of your .db file. (Example: /home/yourname/Documents/filename.db)")
          input("File path: ")
        if (settingsOption == 'e'):
          clear()
          print(Fore.YELLOW + "Export Existing Database File" + Fore.RESET)
          print("Save to: ")
          input("File path: ")
        else:
          invalidInput = True

  # Exit Isadore
  elif (option == 'quit' or option == "q" or option == "exit"):
    clear()
    print(Style.DIM + "Goodbye")
    sleep(1)
    clear()
    break

  # Command unrecognized
  else:
    mainMenuUnrec = True;
