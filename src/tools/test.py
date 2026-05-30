from tools.order_tools import order_tools_list
from tools.menu_tools import menu_tools_list
from tools.menu_tools import search_menu_catalog
from tools.order_tools import get_order_status  

print(order_tools_list)
print(menu_tools_list)

print(search_menu_catalog.invoke({"query": "vegan pasta"}))
print(get_order_status.invoke({"lookup_key": "ORD-201"}))  