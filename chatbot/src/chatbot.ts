import sqlite3 from 'sqlite3';
import { open as openDB } from 'sqlite';
import { v4 as uuidv4 } from 'uuid';
import { DateTime } from 'luxon';
import fs from 'fs';
import path from 'path';
import PDFDocument from 'pdfkit';
import dotenv from 'dotenv';
import axios from 'axios';

// Cargar las variables de entorno
dotenv.config();

// Verificar que la clave de API esté definida
if (!process.env.GROQ_API_KEY) {
    throw new Error("La clave de API de Groq no está definida en .env");
}

const groqApiKey = process.env.GROQ_API_KEY;
const model = 'llama3-8b-8192';

// Datos de combos
const combos = [
    { id: "0001", name: "Combo Hamburguesa Clásica", type: "hamburguesa", ingredients: ["carne", "queso", "pan"], price: 5.99 },
    { id: "0002", name: "Combo Pizza Pepperoni", type: "pizza", ingredients: ["queso", "tomate", "pepperoni"], price: 8.99 },
    { id: "0003", name: "Combo Ensalada César", type: "ensalada", ingredients: ["lechuga", "tomate", "pollo"], price: 6.99 },
    { id: "0004", name: "Combo Hamburguesa Doble", type: "hamburguesa", ingredients: ["doble carne", "queso", "pan"], price: 7.99 },
    { id: "0005", name: "Combo Pizza Vegetariana", type: "pizza", ingredients: ["queso", "tomate", "pimientos", "aceitunas"], price: 8.49 },
    { id: "0006", name: "Combo Wrap de Pollo", type: "wrap", ingredients: ["pollo", "lechuga", "tortilla"], price: 5.49 },
    { id: "0007", name: "Combo Hamburguesa BBQ", type: "hamburguesa", ingredients: ["carne", "queso", "bbq", "pan"], price: 6.99 },
    { id: "0008", name: "Combo Pizza Hawaiana", type: "pizza", ingredients: ["queso", "tomate", "piña", "jamón"], price: 9.99 },
    { id: "0009", name: "Combo Ensalada Griega", type: "ensalada", ingredients: ["lechuga", "queso feta", "aceitunas"], price: 7.49 },
    { id: "0010", name: "Combo Tacos", type: "tacos", ingredients: ["carne", "queso", "tortilla"], price: 5.99 },
    { id: "0011", name: "Combo Hamburguesa Pollo", type: "hamburguesa", ingredients: ["pollo", "queso", "pan"], price: 6.49 },
    { id: "0012", name: "Combo Pizza Cuatro Quesos", type: "pizza", ingredients: ["queso mozzarella", "queso cheddar", "queso azul", "queso parmesano"], price: 10.49 },
    { id: "0013", name: "Combo Ensalada de Atún", type: "ensalada", ingredients: ["lechuga", "atún", "tomate"], price: 7.99 },
    { id: "0014", name: "Combo Burrito", type: "burrito", ingredients: ["carne", "frijoles", "arroz", "tortilla"], price: 6.99 },
    { id: "0015", name: "Combo Hamburguesa Vegana", type: "hamburguesa", ingredients: ["hamburguesa vegana", "queso vegano", "pan"], price: 7.49 },
    { id: "0016", name: "Combo Pizza Mexicana", type: "pizza", ingredients: ["queso", "chorizo", "jalapeños"], price: 9.49 },
    { id: "0017", name: "Combo Ensalada de Frutas", type: "ensalada", ingredients: ["manzana", "pera", "uva"], price: 5.99 },
    { id: "0018", name: "Combo Sushi", type: "sushi", ingredients: ["arroz", "pescado", "alga"], price: 12.99 },
    { id: "0019", name: "Combo Hot Dog", type: "hot dog", ingredients: ["salchicha", "pan", "mostaza"], price: 4.99 },
    { id: "0020", name: "Combo Nuggets de Pollo", type: "nuggets", ingredients: ["pollo", "salsa"], price: 6.49 },
];

// Datos de ítems individuales
const individualItems = [
    { id: "0021", name: "Papas Fritas", price: 1.99 },
    { id: "0022", name: "Pera", price: 0.99 },
    { id: "0023", name: "Refresco", price: 1.49 },
    { id: "0024", name: "Helado", price: 2.49 },
    { id: "0025", name: "Agua", price: 0.99 },
];

// Función para generar un ID de usuario
function generateUserId(): string {
    return uuidv4();
}

// Función para guardar datos en la base de datos
async function saveToDB(
    userId: string,
    comboId: string,
    comboQuantity: number,
    comboPrice: number,
    productId: string,
    productQuantity: number,
    productPrice: number
): Promise<void> {
    const db = await openDB({
        filename: 'chatbotdata.db',
        driver: sqlite3.Database
    });

    const date = DateTime.now().toFormat('yyyy-MM-dd HH:mm:ss');

    await db.run(`
        INSERT INTO Productos_Comprados (user_id, combo_id, combo_quantity, combo_price, product_id, product_quantity, product_price, purchase_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [userId, comboId, comboQuantity, comboPrice, productId, productQuantity, productPrice, date]
    );

    await db.close();
}

// Función para crear una factura en PDF
async function createInvoice(
    userId: string,
    combo: { name: string; price: number; },
    comboQuantity: number,
    additionalItems: { name: string; price: number; quantity: number; id: string; }[]
): Promise<string> {
    const now = DateTime.now();
    const invoiceDate = now.toFormat('yyyy-MM-dd');
    const invoiceTime = now.toFormat('HH-mm-ss');
    const folderPath = 'Facturas';
    const filename = path.join(folderPath, `factura_${userId}_${invoiceDate}_${invoiceTime}.pdf`);

    if (!fs.existsSync(folderPath)) {
        fs.mkdirSync(folderPath);
    }

    const doc = new PDFDocument();
    doc.pipe(fs.createWriteStream(filename));
    doc.fontSize(12).text(`Factura para el Usuario: ${userId}`, { align: 'left' });
    doc.text(`Fecha: ${invoiceDate} Hora: ${invoiceTime}`);
    doc.text('===================================');
    doc.text('Detalle del Pedido:');

    let y = 130;
    const comboTotal = combo.price * comboQuantity;
    doc.text(`Combo: ${combo.name} x${comboQuantity} - $${comboTotal.toFixed(2)}`, { align: 'left' });
    y += 20;

    for (const item of additionalItems) {
        const itemTotal = item.price * item.quantity;
        doc.text(`Ítem: ${item.name} x${item.quantity} - $${itemTotal.toFixed(2)}`, { align: 'left' });
        y += 20;
    }

    doc.text('===================================');
    doc.text(`Total: $${(comboTotal + additionalItems.reduce((sum, item) => sum + item.price * item.quantity, 0)).toFixed(2)}`, { align: 'left' });
    doc.end();

    return filename;
}

// Función para obtener la respuesta del modelo Groq
async function getGroqChatCompletion(message: string) {
    const response = await axios.post('https://api.groq.com/chat/completions', {
        messages: [
            { role: "user", content: message }
        ],
        model: model
    }, {
        headers: {
            'Authorization': `Bearer ${groqApiKey}`,
            'Content-Type': 'application/json'
        }
    });
    return response.data;
}

// Función principal del chatbot
async function chat() {
    const userId = generateUserId();
    console.log(`Bienvenido! Tu ID de usuario es ${userId}. Puedes empezar a hacer preguntas o hacer un pedido.`);

    while (true) {
        const userInput = prompt("\n¿En qué puedo ayudarte hoy? ")?.toLowerCase() || '';
        if (['salir', 'exit', 'quit'].includes(userInput)) {
            console.log("Gracias por usar el chatbot. ¡Hasta luego!");
            break;
        }

        const chatCompletion = await getGroqChatCompletion(userInput);
        const response = chatCompletion.choices[0]?.message?.content || "No tengo una respuesta para eso.";
        console.log(response);

        const recommendedCombos = combos.filter(combo => combo.type.includes(userInput) || combo.ingredients.some(ingredient => userInput.includes(ingredient)));
        if (recommendedCombos.length === 0) {
            console.log("No tenemos recomendaciones basadas en tu entrada.");
        } else {
            console.log("\nAquí tienes algunas recomendaciones para combos:\n");
            recommendedCombos.forEach((option, i) => console.log(`${String.fromCharCode(65 + i)}. ${option.name} - $${option.price.toFixed(2)}`));

            const choice = prompt("\nSelecciona un combo (A, B, C, etc.) o elige 'N' para no añadir nada: ")?.toUpperCase() || '';
            if (choice === 'N') {
                console.log("No se ha añadido ningún combo. Finalizando el pedido.");
                break;
            }

            if (choice >= 'A' && choice <= String.fromCharCode(65 + recommendedCombos.length - 1)) {
                const selectedCombo = recommendedCombos[choice.charCodeAt(0) - 65];
                const comboQuantity = parseInt(prompt(`¿Cuántos ${selectedCombo.name} quieres? `) || '0', 10);

                const additionalItems: { name: string; price: number; quantity: number; id: string; }[] = [];
                while (true) {
                    console.log("\n¿Deseas añadir algo más? (Escribe el nombre del ítem o 'no' para finalizar)");
                    individualItems.forEach((item, i) => console.log(`${String.fromCharCode(65 + i)}. ${item.name} - $${item.price.toFixed(2)}`));

                    const itemChoice = prompt("Selecciona un ítem (A, B, C, etc.) o elige 'no' para finalizar: ")?.toUpperCase() || '';

                    if (itemChoice === 'NO') {
                        break;
                    }

                    if (itemChoice >= 'A' && itemChoice <= String.fromCharCode(65 + individualItems.length - 1)) {
                        const itemIndex = itemChoice.charCodeAt(0) - 65;
                        const item = individualItems[itemIndex];
                        const itemQuantity = parseInt(prompt(`¿Cuántos ${item.name} quieres? `) || '0', 10);
                        additionalItems.push({ name: item.name, price: item.price, quantity: itemQuantity, id: item.id });
                    } else {
                        console.log("Ítem no reconocido. Por favor, prueba nuevamente.");
                    }
                }

                const totalPrice = selectedCombo.price * comboQuantity + additionalItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
                console.log(`\nTotal a pagar: $${totalPrice.toFixed(2)}`);

                for (const item of additionalItems) {
                    await saveToDB(userId, selectedCombo.id, comboQuantity, selectedCombo.price, item.id, item.quantity, item.price);
                }

                const filename = await createInvoice(userId, selectedCombo, comboQuantity, additionalItems);
                console.log(`Tu factura ha sido generada: ${filename}`);
            } else {
                console.log("Selección no válida. Intenta de nuevo.");
            }
        }
    }
}

chat();
