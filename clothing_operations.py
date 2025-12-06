# ashari-bot/clothing_operations.py

import sqlite3
import os
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any
from config.clothing_store import get_clothing_config

# Initialize database connection
def init_database():
    """Initialize the SQLite3 database for clothing items"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clothing_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            size TEXT NOT NULL,
            gender TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lots (
            lot_id VARCHAR(20) PRIMARY KEY,
            lot_name VARCHAR(255) NOT NULL,
            lot_description TEXT,
            lot_category VARCHAR(100),
            lot_tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lot_items (
            lot_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id VARCHAR(20) NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (lot_id) REFERENCES lots(lot_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES clothing_items(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lot_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id VARCHAR(20) NOT NULL,
            sale_price DECIMAL(10,2) NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sold_by VARCHAR(100),
            buyer_name VARCHAR(255),
            buyer_email VARCHAR(255),
            FOREIGN KEY (lot_id) REFERENCES lots(lot_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            sale_price DECIMAL(10,2) NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sold_by VARCHAR(100),
            buyer_name VARCHAR(255),
            buyer_email VARCHAR(255),
            FOREIGN KEY (item_id) REFERENCES clothing_items(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_clothing_item(name: str, brand: str, size: str, gender: str, price: float) -> int:
    """Insert a clothing item into the database"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO clothing_items (name, brand, size, gender, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, brand, size, gender, price))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
        
    except Exception as e:
        print(f"Error inserting clothing item: {str(e)}")
        conn.rollback()
        conn.close()
        return None

def insert_lot(lot_id: str, lot_name: str, lot_description: str = "", lot_category: str = "", lot_tags: str = "") -> bool:
    """Insert a lot into the database"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO lots (lot_id, lot_name, lot_description, lot_category, lot_tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (lot_id, lot_name, lot_description, lot_category, lot_tags))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error inserting lot: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def link_item_to_lot(lot_id: str, item_id: int, quantity: int = 1) -> bool:
    """Link an item to a lot"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO lot_items (lot_id, item_id, quantity)
            VALUES (?, ?, ?)
        ''', (lot_id, item_id, quantity))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error linking item to lot: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def record_lot_sale(lot_id: str, sale_price: float, sold_by: str = None, buyer_name: str = None, buyer_email: str = None) -> bool:
    """Record a sale of a lot"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO lot_sales (lot_id, sale_price, sold_by, buyer_name, buyer_email)
            VALUES (?, ?, ?, ?, ?)
        ''', (lot_id, sale_price, sold_by, buyer_name, buyer_email))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error recording lot sale: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def get_all_items() -> List[Dict[str, Any]]:
    """Get all clothing items"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM clothing_items')
        items = cursor.fetchall()
        
        result = []
        for item in items:
            result.append({
                'id': item[0],
                'name': item[1],
                'brand': item[2],
                'size': item[3],
                'gender': item[4],
                'price': item[5],
                'created_at': item[6],
                'updated_at': item[7]
            })
        
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error retrieving items: {str(e)}")
        conn.close()
        return []

def get_all_lots() -> List[Dict[str, Any]]:
    """Get all lots"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM lots')
        lots = cursor.fetchall()
        
        result = []
        for lot in lots:
            result.append({
                'lot_id': lot[0],
                'lot_name': lot[1],
                'lot_description': lot[2],
                'lot_category': lot[3],
                'lot_tags': lot[4],
                'created_at': lot[5],
                'updated_at': lot[6]
            })
        
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error retrieving lots: {str(e)}")
        conn.close()
        return []

def get_all_sales() -> List[Dict[str, Any]]:
    """Get all sales"""
    config = get_clothing_config()
    conn = sqlite3.connect(config["DATABASE"])
    cursor = conn.cursor()
    
    try:
        # Get lot sales
        cursor.execute('SELECT * FROM lot_sales')
        lot_sales = cursor.fetchall()
        
        # Get item sales
        cursor.execute('SELECT * FROM item_sales')
        item_sales = cursor.fetchall()
        
        result = {
            'lot_sales': [],
            'item_sales': []
        }
        
        for sale in lot_sales:
            result['lot_sales'].append({
                'sale_id': sale[0],
                'lot_id': sale[1],
                'sale_price': sale[2],
                'sale_date': sale[3],
                'sold_by': sale[4],
                'buyer_name': sale[5],
                'buyer_email': sale[6]
            })
        
        for sale in item_sales:
            result['item_sales'].append({
                'sale_id': sale[0],
                'item_id': sale[1],
                'sale_price': sale[2],
                'sale_date': sale[3],
                'sold_by': sale[4],
                'buyer_name': sale[5],
                'buyer_email': sale[6]
            })
        
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error retrieving sales: {str(e)}")
        conn.close()
        return {}
