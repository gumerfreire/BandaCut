# BandaCut

App de Streamlit escrita en Python para la optimización de perfiles 1D. El código resuelve un problema tipo Cutting Stock Problem 1D mediante un algoritmo tipo "greedy" básico.

La entrada de datos se hace a través de tablas de datos en Excel, que deben contener las columnas "Longitud" y "Unidades", indicando las medidas y unidades de piezas de corte que se desean optimizar a partir de perfiles en bruto, cuya longitud se introduce directamente en la interfaz de la app Streamlit.

La app permite la optimización de múltiples tablas al mismo tiempo, incluyendo cada tabla en una hoja del archivo xlsx introducido. Los resultados se dan en pantalla, en archivos de texto individuales, o agrupados en un archivo ZIP en caso de que se optimicen varias tablas de corte al mismo tiempo.
