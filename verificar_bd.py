#!/usr/bin/env python3
"""
Script para verificar el estado de la base de datos
"""
import sqlite3
import os

def verificar_base_datos():
    if not os.path.exists('ia_servicio.db'):
        print("❌ Base de datos NO existe")
        return
    
    print("✅ Base de datos existe\n")
    
    conn = sqlite3.connect('ia_servicio.db')
    cursor = conn.cursor()
    
    # Verificar usuarios
    print("📊 USUARIOS:")
    print("-" * 60)
    usuarios = cursor.execute("SELECT user_id, LENGTH(pdf_text), phone_number FROM usuarios").fetchall()
    
    if not usuarios:
        print("  No hay usuarios registrados")
    else:
        for user_id, pdf_len, phone in usuarios:
            print(f"  User ID: {user_id}")
            print(f"  PDF: {pdf_len if pdf_len else 0} caracteres")
            print(f"  Teléfono: {phone if phone else 'No registrado'}")
            print("-" * 60)
    
    # Verificar llamadas
    print("\n📞 LLAMADAS:")
    print("-" * 60)
    llamadas = cursor.execute("""
        SELECT id, user_id, estado, transcripcion, LENGTH(respuesta), created_at 
        FROM llamadas
        ORDER BY created_at DESC
    """).fetchall()
    
    if not llamadas:
        print("  No hay llamadas registradas")
    else:
        for call_id, user_id, estado, trans, resp_len, created in llamadas:
            print(f"  ID: {call_id}")
            print(f"  User: {user_id}")
            print(f"  Estado: {estado}")
            print(f"  Transcripción: {trans if trans else 'Sin transcribir'}")
            print(f"  Respuesta: {resp_len if resp_len else 0} caracteres")
            print(f"  Creada: {created}")
            print("-" * 60)
    
    conn.close()

if __name__ == '__main__':
    verificar_base_datos()
