# views/forms/form_pago_credito.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal

from config import load_styles, load_svg_icon, format_miles_colombian_int, parse_miles_colombian, STYLES_DIR, ASSETS_DIR, DYNAMIC_DATA_BASE_DIR
from utils.message_boxes import show_success, show_error, show_warning, show_info
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from collections import defaultdict 
from config import HOY, HOY_STR 


# IMPORTAR AHORA DESDE EL NUEVO ARCHIVO ESPECÍFICO DE PAGOS
from utils.recibo_generator_pago import generar_recibo_solo_pagos

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Evita que se cambie el valor al hacer scroll

class FormPagoCredito(QWidget):
    operation_registered = Signal()
    def __init__(self, db_manager, assistant_page = None):
        super().__init__()
        self.db = db_manager
        self.assistant_page = assistant_page
        self.socios_data = []
        self.pagos_widgets = []  # [(combo_socio, letras_container, wrapper_widget)]

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(20, 0, 20, 30)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)


        # "Recibí de:"
        lbl_recibi = QLabel("Recibí de:")
        lbl_recibi.setObjectName("FormLabel")
        self.combo_recibi_de = NoScrollComboBox()
        self.combo_recibi_de.setObjectName("ComboRecibiDe")
        self.combo_recibi_de.setMinimumHeight(50)
        self.combo_recibi_de.setMaximumHeight(50)
        self.combo_recibi_de.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(lbl_recibi)
        main_layout.addWidget(self.combo_recibi_de)

        # Sección dinámicos de pagos
        pagos_label = QLabel("Pagos a registrar:")
        pagos_label.setObjectName("FormLabel")
        main_layout.addWidget(pagos_label)

        self.pagos_container = QVBoxLayout()
        self.pagos_container.setSpacing(12)
        main_layout.addLayout(self.pagos_container)

        # Botón para agregar socio que pagará
        self.btn_agregar_pago = QPushButton(" Agregar pago de socio")
        self.btn_agregar_pago.setObjectName("AddPagoButton")
        self.btn_agregar_pago.setIcon(load_svg_icon("icons/plus.svg"))
        self.btn_agregar_pago.setIconSize(QSize(20, 20))
        self.btn_agregar_pago.setMinimumHeight(36)
        self.btn_agregar_pago.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_agregar_pago.clicked.connect(self.agregar_pago)
        main_layout.addWidget(self.btn_agregar_pago, alignment=Qt.AlignLeft)

        # Espacio y botón registrar
        main_layout.addStretch()
        self.btn_registrar = QPushButton("Registrar Pago")
        self.btn_registrar.setObjectName("RegisterButton")
        self.btn_registrar.setMinimumHeight(44)
        self.btn_registrar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_registrar.clicked.connect(self.on_register)
        main_layout.addWidget(self.btn_registrar, alignment=Qt.AlignHCenter)

        # Carga inicial
        self.load_socios()

        # Aplica estilos
        qss_path = os.path.join(
            STYLES_DIR, "forms", "form_pago_credito.qss"
        )
        load_styles(self, qss_path)

    def load_socios(self):
        """Carga lista de socios para combo_recibi_de."""
        try:
            self.socios_data = self.db.get_all_members_full()
            self.combo_recibi_de.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                self.combo_recibi_de.addItem(nombre, userData=socio)
        except Exception as e:
            show_error(self, "", f"Error cargando socios:\n{e}")

    def agregar_pago(self):
        """Agrega bloque para un socio + sus letras a pagar."""
        # Combo socio
        combo = NoScrollComboBox()
        combo.setObjectName("ComboSocioPago")
        combo.setMinimumHeight(36)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for socio in self.socios_data:
            combo.addItem(f"{socio['nombres']} {socio['apellidos']}", userData=socio)

        # Botón agregar letra
        btn_add_letra = QPushButton(" Agregar letra a pagar")
        btn_add_letra.setObjectName("AddLetraButton")
        btn_add_letra.setIcon(load_svg_icon("icons/plus.svg"))
        btn_add_letra.setIconSize(QSize(16, 16))
        btn_add_letra.setMinimumHeight(36)
        btn_add_letra.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Contenedor dinámico de letras
        letras_container = QVBoxLayout()
        letras_container.setSpacing(8)

        def agregar_letra():
            letra_row = QHBoxLayout()
            letra_row.setContentsMargins(0,0,0,0)

            letra_combo = NoScrollComboBox()
            letra_combo.setObjectName("LetraCombo")
            letra_combo.setMinimumHeight(34)
            letra_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            socio = combo.currentData()
            if socio:
                letras = self.db.get_letras_by_socio_id(socio['id'])
                if not letras:
                    show_info(self, "Sin créditos", "Este socio no tiene letras activas.")
                    return
                for l in letras:
                    texto = (
                        f"Letra {l['letra']}  ·  "
                        f"${format_miles_colombian_int(l['capital'])}  ·  "
                        f"{l['no_cuotas']} cuotas"
                    )
                    letra_combo.addItem(texto, userData=l)

            # --- INPUT ABONO CAPITAL (Nuevo con formato en tiempo real) ---
            abono_input = QLineEdit()
            abono_input.setObjectName("AbonoInput")
            abono_input.setPlaceholderText("$ Abono capital")
            abono_input.setAlignment(Qt.AlignRight)
            abono_input.setFixedHeight(34)
            abono_input.setFixedWidth(140) 

            def on_abono_changed(text):
                # Usamos las funciones de config.py para limpiar y formatear
                raw = parse_miles_colombian(text)
                formatted = format_miles_colombian_int(raw)
                if formatted != text:
                    abono_input.blockSignals(True)
                    abono_input.setText(formatted)
                    # Mantenemos el cursor al final para que no salte al inicio
                    abono_input.setCursorPosition(len(formatted))
                    abono_input.blockSignals(False)

            abono_input.textChanged.connect(on_abono_changed)       

            cuotas_input = QLineEdit()
            cuotas_input.setObjectName("CuotasInput")
            cuotas_input.setPlaceholderText("# Cuotas")
            cuotas_input.setAlignment(Qt.AlignRight)
            cuotas_input.setFixedHeight(34)
            cuotas_input.setFixedWidth(90)

            btn_delete_letra = QPushButton("")
            btn_delete_letra.setObjectName("DeleteLetraButton")
            btn_delete_letra.setIcon(load_svg_icon("icons/x.svg"))
            btn_delete_letra.setIconSize(QSize(16,16))  
            btn_delete_letra.setFixedSize(25,25)
            btn_delete_letra.setToolTip("Eliminar esta letra")
            btn_delete_letra.clicked.connect(lambda: letra_row_widget.setParent(None))

            letra_row.addWidget(letra_combo)
            letra_row.addWidget(abono_input) # <--- AGREGAMOS EL INPUT AQUÍ
            letra_row.addWidget(cuotas_input)
            letra_row.addWidget(btn_delete_letra)

            letra_row_widget = QWidget()
            letra_row_widget.setLayout(letra_row)
            letras_container.addWidget(letra_row_widget)

        btn_add_letra.clicked.connect(agregar_letra)

        # Botón eliminar todo el pago
        btn_delete_pago = QPushButton("")
        btn_delete_pago.setObjectName("DeletePagoButton")
        btn_delete_pago.setIcon(load_svg_icon("icons/x.svg"))
        btn_delete_pago.setIconSize(QSize(20,20))
        btn_delete_pago.setFixedSize(28,28)
        btn_delete_pago.setToolTip("Eliminar este pago")

        # Layout socio + acciones
        socio_row = QHBoxLayout()
        socio_row.setContentsMargins(0,0,0,0)
        socio_row.addWidget(combo)
        socio_row.addWidget(btn_add_letra)
        socio_row.addWidget(btn_delete_pago)

        wrapper_layout = QVBoxLayout()
        wrapper_layout.addLayout(socio_row)
        wrapper_layout.addLayout(letras_container)

        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper_layout)
        self.pagos_container.addWidget(wrapper_widget)

        # Conecta eliminación
        btn_delete_pago.clicked.connect(lambda: wrapper_widget.setParent(None))
        

    def on_register(self):
        """
        Registra pagos validando exclusividad y generando un reporte HTML detallado.
        """
        recibi = self.combo_recibi_de.currentData()
        if not recibi:
            show_warning(self, "", "Debe seleccionar quién entrega el dinero.")
            return

        # Estructuras de datos
        pagos_consolidados_para_recibo = {}
        reporte_global = {} # Diccionario: { "Nombre Socio": ["Acción 1", "Acción 2"] }
        
        # Recolectar widgets activos
        current_pagos_widgets = []
        for i in range(self.pagos_container.count()):
            wrapper = self.pagos_container.itemAt(i).widget()
            if wrapper:
                combo = wrapper.findChild(NoScrollComboBox, "ComboSocioPago")
                wrapper_layout = wrapper.layout()
                if wrapper_layout.count() > 1:
                    letras_container = wrapper_layout.itemAt(1)
                    current_pagos_widgets.append((combo, letras_container, wrapper))

        if not current_pagos_widgets:
            show_warning(self, "", "Agrega al menos un pago.")
            return

        # --- FASE 1: VALIDACIÓN Y PREPARACIÓN ---
        ops_pendientes = [] 
        
        try:
            cursor = self.db.conn.cursor()
            tasa_mora_str = self.db.get_config_value("porcentaje_mora")
            tasa_mora = float(tasa_mora_str) if tasa_mora_str else 0.02
            
            # Headers Recibo
            cursor.execute("INSERT INTO recibos (socio_id) VALUES (?)", (recibi['id'],))
            recibo_id = cursor.lastrowid
            fecha_actual = HOY_STR
            hoy_dt = HOY
            saldo_caja = self.db.get_config_value_as_int("saldo_en_caja")

            for combo, letras_container, _ in current_pagos_widgets:
                socio_selected = combo.currentData()
                if not socio_selected: continue
                socio_full = next((s for s in self.socios_data if s["id"] == socio_selected['id']), None)
                nombre_socio = f"{socio_full['nombres']} {socio_full['apellidos']}"

                for i in range(letras_container.count()):
                    w = letras_container.itemAt(i).widget()
                    letra_selected = w.findChild(NoScrollComboBox, "LetraCombo").currentData()
                    if not letra_selected: continue

                    # Inputs
                    abono_text = w.findChild(QLineEdit, "AbonoInput").text()
                    cuotas_text = w.findChild(QLineEdit, "CuotasInput").text()
                    
                    dinero_abono = parse_miles_colombian(abono_text) if abono_text else 0
                    try: n_cuotas_manual = int(cuotas_text) if cuotas_text else 0
                    except: n_cuotas_manual = 0

                    if dinero_abono == 0 and n_cuotas_manual == 0: continue

                    letra_id = letra_selected['letra']

                    # --- VALIDACIÓN DE EXCLUSIVIDAD ---
                    if dinero_abono > 0 and n_cuotas_manual > 0:
                        show_error(self, "Campos Excluyentes", 
                                   f"En el pago de {nombre_socio} (Letra {letra_id}):\n\n"
                                   "No puede llenar 'Abono Capital' y '# Cuotas' al mismo tiempo.\n"
                                   "• Use '# Cuotas' para pagar cuotas específicas.\n"
                                   "• Use 'Abono Capital' para barrido automático o reducción de capital.")
                        return # Detener todo

                    # Preparar entrada recibo
                    key_recibo = f"{letra_id}_general"
                    if key_recibo not in pagos_consolidados_para_recibo:
                        saldo_ini = self.db.get_deuda_capital_actual(letra_id)
                        pagos_consolidados_para_recibo[key_recibo] = {
                            'socio_data': socio_full, 'letra_id': letra_id,
                            'nro_cuotas_pagadas_start': 0, 'nro_cuotas_pagadas_end': 0,
                            'valor_capital_consolidado': 0, 'interes_consolidado': 0, 'mora_consolidada': 0,
                            'saldo_capital_antes_pago': saldo_ini, 'saldo_capital_despues_pago': 0
                        }
                    
                    # ==============================================================================
                    # CASO A: PAGO POR NÚMERO DE CUOTAS
                    # ==============================================================================
                    if n_cuotas_manual > 0:
                        cursor.execute(
                            "SELECT nro_cuota, valor_cuota, interes_mes, cuota_mensual, saldo_capital, fecha_vencimiento "
                            "FROM liquidaciones WHERE credito_letra = ? AND fecha_pago IS NULL "
                            "ORDER BY nro_cuota LIMIT ?", (letra_id, n_cuotas_manual)
                        )
                        filas = cursor.fetchall()
                        
                        if len(filas) < n_cuotas_manual:
                            show_error(self, "Error", f"No hay suficientes cuotas pendientes para pagar {n_cuotas_manual}.")
                            return

                        cuotas_a_pagar = []
                        mensajes_accion = []

                        for fila in filas:
                            mora_calculada = 0
                            fecha_venc_dt = datetime.strptime(fila['fecha_vencimiento'], "%Y-%m-%d").date()
                            fecha_limite_mora = fecha_venc_dt + relativedelta(months=+1)
                            
                            info_mora = ""
                            if hoy_dt > fecha_limite_mora:
                                mora_calculada = int(fila['valor_cuota'] * tasa_mora)
                                # Texto rojo para la mora
                                info_mora = f" <span style='color:#d9534f'>(+Mora ${format_miles_colombian_int(mora_calculada)})</span>"

                            costo_total = fila['valor_cuota'] + fila['interes_mes'] + mora_calculada
                            
                            cuotas_a_pagar.append({
                                'nro': fila['nro_cuota'], 'monto': costo_total, 'mora': mora_calculada,
                                'cap': fila['valor_cuota'], 'int': fila['interes_mes']
                            })
                            # Mensaje formateado
                            mensajes_accion.append(f"Cuota #{fila['nro_cuota']} (${format_miles_colombian_int(costo_total)}){info_mora}")
                        
                        ops_pendientes.append({
                            'tipo': 'CUOTAS_MANUAL',
                            'socio_data': socio_full, 'letra_id': letra_id,
                            'items': cuotas_a_pagar,
                            'mensajes': mensajes_accion
                        })

                    # ==============================================================================
                    # CASO B: ABONO (CASCADA AUTOMÁTICA)
                    # ==============================================================================
                    elif dinero_abono > 0:
                        pendientes = self.db.get_pending_installments(letra_id)
                        vencidas_a_pagar = [] 
                        
                        # 1. Identificar Vencidas
                        for cuota in pendientes:
                            fecha_venc_dt = datetime.strptime(cuota['fecha_vencimiento'], "%Y-%m-%d").date()
                            if fecha_venc_dt < hoy_dt: 
                                cap = cuota['valor_cuota']
                                ints = cuota['interes_mes']
                                m_calc = 0
                                fecha_limite = fecha_venc_dt + relativedelta(months=+1)
                                if hoy_dt > fecha_limite:
                                    m_calc = int(cap * tasa_mora)
                                
                                total_row = cap + ints + m_calc
                                vencidas_a_pagar.append({
                                    'data': cuota, 'costo': total_row, 'mora': m_calc
                                })
                            else:
                                break
                        
                        # 2. Validación Estricta
                        temp_dinero = dinero_abono
                        pagables_count = 0
                        costo_acumulado = 0
                        
                        for v in vencidas_a_pagar:
                            if temp_dinero >= v['costo']:
                                temp_dinero -= v['costo']
                                costo_acumulado += v['costo']
                                pagables_count += 1
                            else:
                                if pagables_count == 0:
                                    show_error(self, "Abono Insuficiente", 
                                        f"El dinero (${format_miles_colombian_int(dinero_abono)}) no cubre la primera cuota vencida "
                                        f"#{v['data']['nro_cuota']} (${format_miles_colombian_int(v['costo'])}).\n\n"
                                        "Operación rechazada.")
                                    return
                                else:
                                    show_warning(self, "Monto Incompleto", 
                                        f"El abono paga {pagables_count} cuotas vencidas, pero sobra un remanente de "
                                        f"${format_miles_colombian_int(temp_dinero)} que no cubre la siguiente.\n\n"
                                        f"Ajuste el abono a ${format_miles_colombian_int(costo_acumulado)} o complete el valor.")
                                    return

                        # 3. Calcular Remanente Capital
                        remanente_capital = 0
                        if temp_dinero > 0:
                            deuda_actual = self.db.get_deuda_capital_actual(letra_id)
                            # Restamos el capital de las vencidas que vamos a pagar
                            capital_vencidas_pagadas = sum([v['data']['valor_cuota'] for v in vencidas_a_pagar[:pagables_count]])
                            deuda_futura_real = deuda_actual - capital_vencidas_pagadas
                            
                            if temp_dinero > deuda_futura_real:
                                show_warning(self, "Exceso de Pago", 
                                             f"El saldo restante es ${format_miles_colombian_int(deuda_futura_real)}. "
                                             f"Se cobrará solo eso. Devuelva el excedente: ${format_miles_colombian_int(temp_dinero - deuda_futura_real)}.")
                                temp_dinero = deuda_futura_real
                            
                            remanente_capital = temp_dinero

                        # Preparar mensajes de reporte
                        mensajes_accion = []
                        for i in range(pagables_count):
                            v = vencidas_a_pagar[i]
                            info = f"Vencida #{v['data']['nro_cuota']} (${format_miles_colombian_int(v['costo'])})"
                            if v['mora'] > 0: 
                                info += f" <span style='color:#d9534f'>(+Mora ${format_miles_colombian_int(v['mora'])})</span>"
                            mensajes_accion.append(info)
                        
                        if remanente_capital > 0:
                            mensajes_accion.append(f"Abono Capital: <b>${format_miles_colombian_int(remanente_capital)}</b>")

                        ops_pendientes.append({
                            'tipo': 'ABONO_CASCADA',
                            'socio_data': socio_full, 'letra_id': letra_id,
                            'vencidas': vencidas_a_pagar[:pagables_count],
                            'capital_puro': remanente_capital,
                            'mensajes': mensajes_accion
                        })

            # --- FASE 2: EJECUCIÓN ---
            if not ops_pendientes: return

            cursor = self.db.conn.cursor()
            
            # Recorrer operaciones validadas
            for op in ops_pendientes:
                letra_id = op['letra_id']
                socio_data = op['socio_data']
                nombre_socio = f"{socio_data['nombres']} {socio_data['apellidos']}"
                
                # Agrupar mensajes para el reporte final
                if nombre_socio not in reporte_global:
                    reporte_global[nombre_socio] = []
                reporte_global[nombre_socio].extend(op['mensajes'])

                key_recibo = f"{letra_id}_general"
                dict_recibo = pagos_consolidados_para_recibo[key_recibo]

                if op['tipo'] == 'CUOTAS_MANUAL':
                    items = op['items']
                    dict_recibo['nro_cuotas_pagadas_start'] = items[0]['nro']
                    dict_recibo['nro_cuotas_pagadas_end'] = items[-1]['nro']
                    
                    for it in items:
                        cursor.execute("""
                            INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto, abono_mora)
                            VALUES (?, 'pago_credito', ?, ?, ?, ?, ?)
                        """, (recibo_id, socio_data['id'], letra_id, it['nro'], it['monto'], it['mora']))
                        
                        m_flag = 1 if it['mora'] > 0 else 0
                        cursor.execute("""
                            UPDATE liquidaciones SET fecha_pago = DATE('now'), interes_mora = ?, mora_aplicada = ? 
                            WHERE credito_letra=? AND nro_cuota=?
                        """, (it['mora'], m_flag, letra_id, it['nro']))
                        
                        saldo_caja += it['monto']
                        dict_recibo['valor_capital_consolidado'] += it['cap']
                        dict_recibo['interes_consolidado'] += it['int']
                        dict_recibo['mora_consolidada'] += it['mora']
                        
                        self.db.add_to_auxiliar(
                            fecha=fecha_actual, tipo="Pago Credito", socio=nombre_socio,
                            monto=it['monto'], saldo=saldo_caja, recibo=recibo_id, cuota=it['nro'], id_credito=str(letra_id)
                        )

                elif op['tipo'] == 'ABONO_CASCADA':
                    vencidas = op['vencidas']
                    capital_puro = op['capital_puro']
                    
                    # Pagar Vencidas
                    for v in vencidas:
                        nro = v['data']['nro_cuota']
                        costo = v['costo']
                        mora = v['mora']
                        
                        cursor.execute("""
                            INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto, abono_mora)
                            VALUES (?, 'pago_credito', ?, ?, ?, ?, ?)
                        """, (recibo_id, socio_data['id'], letra_id, nro, costo, mora))
                        
                        m_flag = 1 if mora > 0 else 0
                        cursor.execute("""
                            UPDATE liquidaciones SET fecha_pago = DATE('now'), interes_mora = ?, mora_aplicada = ? 
                            WHERE credito_letra=? AND nro_cuota=?
                        """, (mora, m_flag, letra_id, nro))
                        
                        saldo_caja += costo
                        
                        dict_recibo['valor_capital_consolidado'] += v['data']['valor_cuota']
                        dict_recibo['interes_consolidado'] += v['data']['interes_mes']
                        dict_recibo['mora_consolidada'] += mora
                        
                        self.db.add_to_auxiliar(
                            fecha=fecha_actual, tipo="Pago Credito", socio=nombre_socio,
                            monto=costo, saldo=saldo_caja, recibo=recibo_id, cuota=nro, id_credito=str(letra_id)
                        )

                    # Pagar Capital Puro
                    if capital_puro > 0:
                        cursor.execute("""
                            INSERT INTO detalle_recibo (recibo_id, tipo_operacion, socio_id, credito_letra, nro_cuota, monto)
                            VALUES (?, 'pago_credito', ?, ?, 0, ?)
                        """, (recibo_id, socio_data['id'], letra_id, capital_puro))
                        
                        saldo_caja += capital_puro
                        self.db.recalcular_tabla_amortizacion(letra_id, capital_puro)
                        
                        dict_recibo['valor_capital_consolidado'] += capital_puro
                        
                        self.db.add_to_auxiliar(
                            fecha=fecha_actual, tipo="Abono Capital", socio=nombre_socio,
                            monto=capital_puro, saldo=saldo_caja, recibo=recibo_id, cuota=0, id_credito=str(letra_id)
                        )

                    # Etiquetas Recibo Cascada
                    if vencidas:
                        dict_recibo['nro_cuotas_pagadas_start'] = vencidas[0]['data']['nro_cuota']
                        dict_recibo['nro_cuotas_pagadas_end'] = "ABONO" if capital_puro > 0 else vencidas[-1]['data']['nro_cuota']
                    else:
                        dict_recibo['nro_cuotas_pagadas_start'] = "ABONO"
                        dict_recibo['nro_cuotas_pagadas_end'] = "CAPITAL"

                # Saldo final visual (aproximado)
                deuda_aprox = dict_recibo['saldo_capital_antes_pago'] - dict_recibo['valor_capital_consolidado']
                dict_recibo['saldo_capital_despues_pago'] = max(0, int(deuda_aprox))

            # 3. Finalizar
            self.db.set_config_value("saldo_en_caja", str(saldo_caja))
            self.db.conn.commit()

            # --- CONSTRUCCIÓN DEL REPORTE FINAL (HTML) ---
            if reporte_global:
                msg_final = ""
                for nombre, acciones in reporte_global.items():
                    # Nombre en Negrita
                    msg_final += f"<b>{nombre}</b><br>"
                    for accion in acciones:
                        # Sangría y salto de línea HTML
                        msg_final += f"&nbsp;&nbsp;• {accion}<br>"
                    msg_final += "<br>" # Espacio entre socios
                
                # Eliminamos el último <br> extra si se desea, o lo dejamos para espacio
                show_info(self, "Resumen de Transacción", msg_final)

            # Generar Excel
            recibo_path = generar_recibo_solo_pagos(
                db_manager=self.db,
                recibo_id=recibo_id,
                recibi_de_data=recibi,
                pagos_credito_info=list(pagos_consolidados_para_recibo.values())
            )
            
            if recibo_path:
                show_success(self, "Pago Registrado", f"Transacción exitosa. Recibo #{recibo_id}", file_path=recibo_path)
                self.operation_registered.emit()
            
            self.clear_form()

        except Exception as e:
            self.db.conn.rollback()
            show_error(self, "Error", f"Error crítico: {e}")
            import traceback
            traceback.print_exc()

    def refresh(self):
        """Recarga la lista de socios y actualiza los combos existentes."""
        self.load_socios()
        # Actualizar combos de socios existentes
        for combo, letras_container, _ in self.pagos_widgets:
            socio_actual = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for socio in self.socios_data:
                nombre = f"{socio['nombres']} {socio['apellidos']}"
                combo.addItem(nombre, userData=socio)
            # Reestablecer selección si era válida
            if socio_actual:
                for i in range(combo.count()):
                    if combo.itemData(i)['id'] == socio_actual['id']:
                        combo.setCurrentIndex(i)
                        break
            combo.blockSignals(False)

    def clear_form(self):
        """Limpia el formulario y recarga los socios."""
        # Elimina todos los widgets de pago dinámicos
        for i in reversed(range(self.pagos_container.count())):
            widget = self.pagos_container.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Vacía la lista de widgets de pago
        self.pagos_widgets.clear()
        
        # Recarga los socios
        self.load_socios()