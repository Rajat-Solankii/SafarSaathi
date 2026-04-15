# 🚌 Smart Bus Tracking System

A real-time bus tracking and route management web application built using **Flask**. This system allows drivers to broadcast live location updates and passengers to track buses, view routes, and estimate arrival times.

---

## 🚀 Features

### 👨‍✈️ Driver Module
- Create and manage bus routes
- Add multiple stops with coordinates
- Broadcast live location
- Automatically detect route completion

### 🧍 Passenger Module
- Search routes and stops
- Track live bus location
- Get nearest stop information
- View estimated arrival time (ETA)

### 🌐 Core Functionalities
- Location autocomplete using LocationIQ API
- Distance calculation using Haversine formula
- ETA calculation using OpenRouteService API
- JSON-based lightweight data storage

---

## 🏗️ Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript (Templates)
- **APIs Used:**
  - LocationIQ (Autocomplete)
  - OpenRouteService (Routing & ETA)
- **Storage:** JSON files (No database required)

---

## 📁 Project Structure
