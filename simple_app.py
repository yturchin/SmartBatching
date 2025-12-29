import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.dates import DateFormatter
import numpy as np
from dataclasses import dataclass
from typing import List
from enum import Enum
from collections import Counter

# Типы
class PrintType(Enum):
    BW = "Ч/Б"
    COLOR = "Цветная"

class PaperType(Enum):
    PLAIN = "Обычная"
    COATED = "Мелованная"
    RECYCLED = "Переработанная"

class MachineType(Enum):
    ROLL = "Ролевая"
    SHEET = "Листовая"

# Заказ
@dataclass
class Order:
    id: str
    machine_type: MachineType
    print_type: PrintType
    paper_type: PaperType
    roll_width: int
    format: tuple
    book_thickness: int
    deadline: datetime
    quantity: int
    priority: int = 0

# Батч
@dataclass
class Batch:
    id: str
    orders: List[Order]
    print_type: PrintType
    paper_type: PaperType
    
    @property
    def total_quantity(self):
        return sum(o.quantity for o in self.orders)
    
    @property
    def avg_priority(self):
        return sum(o.priority for o in self.orders) / len(self.orders) if self.orders else 0

# Простая система
class SimpleSmartBatching:
    def process(self, orders):
        # Группируем по типу печати
        batches = []
        batch_id = 1
        
        # Сначала срочные
        urgent = [o for o in orders if o.priority > 0]
        if urgent:
            batches.append(Batch(
                f"BATCH-{batch_id:04d}",
                urgent,
                urgent[0].print_type,
                urgent[0].paper_type
            ))
            batch_id += 1
        
        # Потом обычные по типу печати
        normal = [o for o in orders if o.priority == 0]
        for print_type in [PrintType.COLOR, PrintType.BW]:
            same_type = [o for o in normal if o.print_type == print_type]
            if same_type:
                batches.append(Batch(
                    f"BATCH-{batch_id:04d}",
                    same_type,
                    print_type,
                    same_type[0].paper_type
                ))
                batch_id += 1
        
        return {
            'batches': batches,
            'total_orders': len(orders),
            'metrics': {
                'total_batches': len(batches),
                'total_changeovers': len(batches) - 1,
                'total_changeover_time_minutes': (len(batches) - 1) * 20
            }
        }

# Визуализация
class SimpleVisualizer:
    def __init__(self):
        self.colors = {
            'urgent': '#FF0000',
            'COLOR': '#FF9800',
            'BW': '#2196F3'
        }
    
    def plot_gantt(self, result):
        batches = result['batches']
        fig, ax = plt.subplots(figsize=(14, 8))
        
        current_time = datetime.now()
        y_pos = 0
        
        for i, batch in enumerate(batches):
            duration = timedelta(hours=batch.total_quantity / 1000)
            
            # Переналадка
            if i > 0:
                changeover = timedelta(minutes=20)
                ax.barh(y_pos, changeover.total_seconds()/3600,
                       left=current_time, height=0.8,
                       color='#9E9E9E', alpha=0.5)
                current_time += changeover
            
            # Цвет батча
            if batch.avg_priority > 0:
                color = self.colors['urgent']
            elif batch.print_type == PrintType.COLOR:
                color = self.colors['COLOR']
            else:
                color = self.colors['BW']
            
            ax.barh(y_pos, duration.total_seconds()/3600,
                   left=current_time, height=0.8,
                   color=color, alpha=0.7, edgecolor='black')
            
            center = current_time + duration / 2
            ax.text(center, y_pos, f"{batch.id}\\n{len(batch.orders)} зак",
                   ha='center', va='center', fontsize=9, fontweight='bold')
            
            current_time += duration
            y_pos += 1
        
        ax.set_yticks(range(len(batches)))
        ax.set_yticklabels([f"#{i+1}" for i in range(len(batches))])
        ax.set_xlabel('Время', fontsize=11)
        ax.set_title('GANTT CHART', fontsize=14, fontweight='bold')
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
        ax.grid(True, axis='x', alpha=0.3)
        
        legend = [
            mpatches.Patch(color=self.colors['urgent'], label='Срочные'),
            mpatches.Patch(color=self.colors['COLOR'], label='Цветная'),
            mpatches.Patch(color=self.colors['BW'], label='Ч/Б')
        ]
        ax.legend(handles=legend)
        plt.tight_layout()
        return fig
    
    def plot_comparison(self, result):
        metrics = result['metrics']
        total = result['total_orders']
        
        fifo_time = (total - 1) * 20
        smart_time = metrics['total_changeover_time_minutes']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
        
        # Переналадки
        ax1.bar(['FIFO', 'Smart'], 
               [total-1, metrics['total_changeovers']],
               color=['#E53935', '#43A047'])
        ax1.set_ylabel('Переналадок')
        ax1.set_title('Количество переналадок')
        
        # Время
        ax2.bar(['FIFO', 'Smart'],
               [fifo_time/60, smart_time/60],
               color=['#E53935', '#43A047'])
        ax2.set_ylabel('Время (ч)')
        ax2.set_title('Время переналадок')
        
        saved = fifo_time - smart_time
        fig.text(0.5, 0.02, f'Экономия: {saved} мин ({saved/fifo_time*100:.0f}%)',
                ha='center', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        return fig

# STREAMLIT ИНТЕРФЕЙС
st.set_page_config(page_title="Smart Batching", layout="wide")

st.title("🎯 Smart Batching System")
st.markdown("---")

# Инициализация
if 'orders' not in st.session_state:
    st.session_state.orders = [
        Order('URGENT', MachineType.ROLL, PrintType.BW, PaperType.RECYCLED,
              1000, (280, 400), None, datetime.now() + timedelta(days=2), 15000, priority=2),
        Order('COLOR', MachineType.ROLL, PrintType.COLOR, PaperType.COATED,
              1000, (210, 297), None, datetime.now() + timedelta(days=7), 5000),
        Order('BW', MachineType.ROLL, PrintType.BW, PaperType.PLAIN,
              1000, (210, 297), None, datetime.now() + timedelta(days=8), 7000),
    ]

# Боковая панель
st.sidebar.header("Управление")
st.sidebar.write(f"📦 Заказов: {len(st.session_state.orders)}")

if st.sidebar.button("🔄 Сбросить примеры"):
    st.session_state.orders = [
        Order('URGENT', MachineType.ROLL, PrintType.BW, PaperType.RECYCLED,
              1000, (280, 400), None, datetime.now() + timedelta(days=2), 15000, priority=2),
        Order('COLOR', MachineType.ROLL, PrintType.COLOR, PaperType.COATED,
              1000, (210, 297), None, datetime.now() + timedelta(days=7), 5000),
        Order('BW', MachineType.ROLL, PrintType.BW, PaperType.PLAIN,
              1000, (210, 297), None, datetime.now() + timedelta(days=8), 7000),
    ]
    st.rerun()

# Добавление заказа
with st.sidebar.form("add_order"):
    st.subheader("➕ Новый заказ")
    order_id = st.text_input("ID", f"ORDER-{len(st.session_state.orders)+1}")
    print_type = st.selectbox("Печать", ["Цветная", "Ч/Б"])
    quantity = st.number_input("Тираж", min_value=1000, value=5000, step=1000)
    priority = st.number_input("Приоритет", min_value=0, value=0)
    
    if st.form_submit_button("Добавить"):
        new_order = Order(
            order_id,
            MachineType.ROLL,
            PrintType.COLOR if print_type == "Цветная" else PrintType.BW,
            PaperType.PLAIN,
            1000, (210, 297), None,
            datetime.now() + timedelta(days=7),
            quantity, priority
        )
        st.session_state.orders.append(new_order)
        st.rerun()

# Обработка
if st.session_state.orders:
    system = SimpleSmartBatching()
    result = system.process(st.session_state.orders)
    viz = SimpleVisualizer()
    
    # Метрики
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Заказов", result['total_orders'])
    col2.metric("🔄 Батчей", result['metrics']['total_batches'])
    col3.metric("⚡ Переналадок", result['metrics']['total_changeovers'])
    
    st.markdown("---")
    
    # Графики
    tab1, tab2 = st.tabs(["📊 Gantt", "📈 Сравнение"])
    
    with tab1:
        fig = viz.plot_gantt(result)
        st.pyplot(fig)
        plt.close()
    
    with tab2:
        fig = viz.plot_comparison(result)
        st.pyplot(fig)
        plt.close()
    
    # Список заказов
    st.markdown("---")
    st.subheader("📋 Заказы")
    for i, order in enumerate(st.session_state.orders, 1):
        cols = st.columns([1, 3, 2, 1])
        cols[0].write(f"**{i}.**")
        cols[1].write(order.id)
        cols[2].write(f"{order.print_type.value}, {order.quantity} шт")
        cols[3].write("🔴" if order.priority > 0 else "🟢")

else:
    st.warning("⚠️ Нет заказов")

st.markdown("---")
st.caption("Smart Batching v1.0")
