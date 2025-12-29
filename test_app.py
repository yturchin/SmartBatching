import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title("🧪 ТЕСТ Streamlit + Matplotlib")

st.write("Если вы видите этот текст - Streamlit работает ✅")

# Простой график
st.subheader("Тест графика")

fig, ax = plt.subplots()
x = [1, 2, 3, 4, 5]
y = [2, 4, 6, 8, 10]
ax.plot(x, y, 'ro-', linewidth=2)
ax.set_title("Простой график")
ax.set_xlabel("X")
ax.set_ylabel("Y")

st.pyplot(fig)
plt.close()

st.success("✅ Если вы видите график выше - визуализация работает!")

# Кнопка
if st.button("Нажми меня"):
    st.balloons()
    st.write("🎉 Интерактивность работает!")
