import os
import sqlite3
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq

# Datos de combos
combos = [
    {"id": "0001", "name": "Combo Hamburguesa Clásica", "type": "hamburguesa", "ingredients": ["carne", "queso", "pan"], "price": 5.99},
    {"id": "0002", "name": "Combo Pizza Pepperoni", "type": "pizza", "ingredients": ["queso", "tomate", "pepperoni"], "price": 8.99},
    {"id": "0003", "name": "Combo Ensalada César", "type": "ensalada", "ingredients": ["lechuga", "tomate", "pollo"], "price": 6.99},
    {"id": "0004", "name": "Combo Hamburguesa Doble", "type": "hamburguesa", "ingredients": ["doble carne", "queso", "pan"], "price": 7.99},
    {"id": "0005", "name": "Combo Pizza Vegetariana", "type": "pizza", "ingredients": ["queso", "tomate", "pimientos", "aceitunas"], "price": 8.49},
    {"id": "0006", "name": "Combo Wrap de Pollo", "type": "wrap", "ingredients": ["pollo", "lechuga", "tortilla"], "price": 5.49},
    {"id": "0007", "name": "Combo Hamburguesa BBQ", "type": "hamburguesa", "ingredients": ["carne", "queso", "bbq", "pan"], "price": 6.99},
    {"id": "0008", "name": "Combo Pizza Hawaiana", "type": "pizza", "ingredients": ["queso", "tomate", "piña", "jamón"], "price": 9.99},
    {"id": "0009", "name": "Combo Ensalada Griega", "type": "ensalada", "ingredients": ["lechuga", "queso feta", "aceitunas"], "price": 7.49},
    {"id": "0010", "name": "Combo Tacos", "type": "tacos", "ingredients": ["carne", "queso", "tortilla"], "price": 5.99},
    {"id": "0011", "name": "Combo Hamburguesa Pollo", "type": "hamburguesa", "ingredients": ["pollo", "queso", "pan"], "price": 6.49},
    {"id": "0012", "name": "Combo Pizza Cuatro Quesos", "type": "pizza", "ingredients": ["queso mozzarella", "queso cheddar", "queso azul", "queso parmesano"], "price": 10.49},
    {"id": "0013", "name": "Combo Ensalada de Atún", "type": "ensalada", "ingredients": ["lechuga", "atún", "tomate"], "price": 7.99},
    {"id": "0014", "name": "Combo Burrito", "type": "burrito", "ingredients": ["carne", "frijoles", "arroz", "tortilla"], "price": 6.99},
    {"id": "0015", "name": "Combo Hamburguesa Vegana", "type": "hamburguesa", "ingredients": ["hamburguesa vegana", "queso vegano", "pan"], "price": 7.49},
    {"id": "0016", "name": "Combo Pizza Mexicana", "type": "pizza", "ingredients": ["queso", "chorizo", "jalapeños"], "price": 9.49},
    {"id": "0017", "name": "Combo Ensalada de Frutas", "type": "ensalada", "ingredients": ["manzana", "pera", "uva"], "price": 5.99},
    {"id": "0018", "name": "Combo Sushi", "type": "sushi", "ingredients": ["arroz", "pescado", "alga"], "price": 12.99},
    {"id": "0019", "name": "Combo Hot Dog", "type": "hot dog", "ingredients": ["salchicha", "pan", "mostaza"], "price": 4.99},
    {"id": "0020", "name": "Combo Nuggets de Pollo", "type": "nuggets", "ingredients": ["pollo", "salsa"], "price": 6.49},
]

# Datos de ítems individuales
individual_items = [
    {"id": "0021", "name": "Papas Fritas", "price": 1.99},
    {"id": "0022", "name": "Pera", "price": 0.99},
    {"id": "0023", "name": "Refresco", "price": 1.49},
    {"id": "0024", "name": "Helado", "price": 2.49},
    {"id": "0025", "name": "Agua", "price": 0.99},
]

def generate_user_id():
    """
    Genera un ID único para el usuario usando UUID.
    """
    return str(uuid.uuid4())

def save_to_db(user_id, combo_id, combo_quantity, combo_price, product_id, product_quantity, product_price):
    db_path = r'C:\Users\jhuom\Documents\[H9]-SOFTWARE\HACKATON\VERCEL SDK-AI Restaurant\chatbotdata.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO Productos_Comprados (user_id, combo_id, combo_quantity, combo_price, product_id, product_quantity, product_price, purchase_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, combo_id, combo_quantity, combo_price, product_id, product_quantity, product_price, date))
    
    conn.commit()
    conn.close()

def create_invoice(user_id, combo, combo_quantity, additional_items):
    now = datetime.now()
    invoice_date = now.strftime('%Y-%m-%d')
    invoice_time = now.strftime('%H-%M-%S')
    folder_path = r'C:\Users\jhuom\Documents\[H9]-SOFTWARE\HACKATON\VERCEL SDK-AI Restaurant\Facturas'
    filename = os.path.join(folder_path, f'factura_{user_id}_{invoice_date}_{invoice_time}.pdf')

    # Verificar si la carpeta 'Facturas' existe
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica", 12)
    c.drawString(30, height - 50, f"Factura para el Usuario: {user_id}")
    c.drawString(30, height - 70, f"Fecha: {invoice_date} Hora: {invoice_time}")
    c.drawString(30, height - 90, "===================================")
    c.drawString(30, height - 110, "Detalle del Pedido:")
    
    y = height - 130
    combo_total = combo["price"] * combo_quantity
    c.drawString(30, y, f"Combo: {combo['name']} x{combo_quantity} - ${combo_total:.2f}")
    y -= 20
    
    for item in additional_items:
        item_total = item["price"] * item["quantity"]
        c.drawString(30, y, f"Ítem: {item['name']} x{item['quantity']} - ${item_total:.2f}")
        y -= 20
    
    c.drawString(30, y, "===================================")
    c.drawString(30, y - 20, f"Total: ${combo_total + sum(item['price'] * item['quantity'] for item in additional_items):.2f}")
    c.save()

    return filename

def chat():
    # Configura el cliente de Groq
    groq_api_key = os.environ['GROQ_API_KEY']
    model = 'llama3-8b-8192'
    groq_chat = ChatGroq(
        groq_api_key=groq_api_key, 
        model_name=model
    )

    system_prompt = 'Eres un chatbot amigable que puede recomendar combos de comida rápida y ayudar a los clientes con sus pedidos.'
    conversational_memory_length = 5

    memory = ConversationBufferWindowMemory(
        k=conversational_memory_length,
        memory_key="chat_history",
        return_messages=True
    )

    user_id = generate_user_id()
    print(f"Bienvenido! Tu ID de usuario es {user_id}. Puedes empezar a hacer preguntas o hacer un pedido.")

    while True:
        user_input = input("\n¿En qué puedo ayudarte hoy? ").lower()
        if user_input in ["salir", "exit", "quit"]:
            print("Gracias por usar el chatbot. ¡Hasta luego!")
            break

        # Construye el prompt del chat usando componentes
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=system_prompt
                ),
                MessagesPlaceholder(
                    variable_name="chat_history"
                ),
                HumanMessagePromptTemplate.from_template(
                    "{human_input}"
                ),
            ]
        )

        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=False,
            memory=memory,
        )

        # Obtención de recomendaciones (simplificada)
        recommended_combos = [combo for combo in combos if combo["type"] in user_input or any(ingredient in user_input for ingredient in combo["ingredients"])]
        if not recommended_combos:
            recommended_combos = [combo for combo in combos if combo["price"] < 7.00]

        if recommended_combos:
            print("\nAquí tienes algunas recomendaciones para combos:\n")
            for i, option in enumerate(recommended_combos):
                print(f"{chr(65 + i)}. {option['name']} - ${option['price']:.2f}")

            choice = input("\nSelecciona un combo (A, B, C, etc.) o elige 'N' para no añadir nada: ").upper()
            if choice == 'N':
                print("No se ha añadido ningún combo. Finalizando el pedido.")
                break

            if choice in [chr(65 + i) for i in range(len(recommended_combos))]:
                selected_combo = recommended_combos[ord(choice) - 65]
                combo_quantity = int(input(f"¿Cuántos {selected_combo['name']} quieres? "))
                combo_price = selected_combo['price']
                
                additional_items = []
                while True:
                    print("\n¿Deseas añadir algo más? (Escribe el nombre del ítem o 'no' para finalizar)")
                    for i, item in enumerate(individual_items):
                        print(f"{chr(65 + i)}. {item['name']} - ${item['price']:.2f}")

                    item_choice = input("Selecciona un ítem (A, B, C, etc.) o elige 'no' para finalizar: ").upper()

                    if item_choice == 'NO':
                        break

                    item_index = ord(item_choice) - 65
                    if 0 <= item_index < len(individual_items):
                        item = individual_items[item_index]
                        item_quantity = int(input(f"¿Cuántos {item['name']} quieres? "))
                        additional_items.append({"name": item['name'], "price": item['price'], "quantity": item_quantity, "id": item['id']})
                    else:
                        print("Ítem no reconocido. Por favor, prueba nuevamente.")

                total_price = combo_price * combo_quantity + sum(item['price'] * item['quantity'] for item in additional_items)
                print(f"\nTotal a pagar: ${total_price:.2f}")

                # Guardar en la base de datos
                for item in additional_items:
                    save_to_db(user_id, selected_combo["id"], combo_quantity, combo_price, item["id"], item["quantity"], item["price"])

                # Crear la factura
                filename = create_invoice(user_id, selected_combo, combo_quantity, additional_items)
                print(f"Factura generada y guardada en la carpeta 'Facturas' como {os.path.basename(filename)}")
            else:
                print("Opción no válida.")
        else:
            print("Lo siento, no tenemos recomendaciones basadas en tu entrada.")

if __name__ == "__main__":
    chat()