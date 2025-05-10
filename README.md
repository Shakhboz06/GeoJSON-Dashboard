# 🌍 GeoJSON Dashboard

A Streamlit-based web application for processing, validating, and visualizing GeoJSON files—complete with duplicate-detection, automated geometry fixes, interactive maps, simulated team comments, and Kafka-driven event publishing. Containerized with Docker & Docker Compose for easy deployment alongside Kafka & Zookeeper.

---

## 🚀 Overview

- **File Upload & Data Preview:** Upload GeoJSON files and display them in a table.
- **Map Visualization:** Show geometries on an interactive map.
- **Duplicate Detection:** Identify and report duplicate geometries.
- **Problematic Geometry Handling:** Detect invalid geometries, explain issues, and attempt automated fixes.

### Optional enhancements:
- **Error Logging** with Loguru.
- **Event-Driven Architecture** using Kafka.
- **Simulated Team Collaboration** via a comments section.

---

## 📂 Project Structure


- backend/
- ├── app.py                  # Main Streamlit app (with inline comments)
- ├── kafka_integration.py    # Kafka producer & event publisher
- ├── requirements.txt        # Python dependencies
- ├── Dockerfile              # Containerization recipe
- ├── docker-compose.yml      # Orchestrates app + Kafka + Zookeeper
- ├── README.md               # ← This file
- └── app.log                 # Generated at runtime by Loguru

---

## ⭐ Features

- **File Upload & Data Preview**
-- Upload .geojson/.json and preview first 10 rows.

- **Parallel Geometry Validation & Correction**
-- Uses concurrent.futures to validate geometries concurrently.

- **Fixes invalid geometries with a zero-width buffer (buffer(0)).**
- **Displays issues for any geometries that remain invalid.**

- **Duplicate Detection**
-- Flags and lists duplicate geometries.

- **Interactive Map**
-- Renders valid GeoJSON on a Folium map (via streamlit-folium), centered on the data’s centroid.

- **Simulated Collaboration**
-- Comments section stored in session state for team notes.

- **Kafka Event Publishing**
-- Publishes metadata events (filename, processing_time, total_features) to a Kafka topic (geojson_upload_events).
