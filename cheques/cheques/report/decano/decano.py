# Copyright (c) 2013, Diamo and contributors
# For license information, please see license.txt
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from erpnext.accounts.report.financial_statements import (get_period_list, get_data)
from .utils import MESES


def execute(filters=None):
    # Buscamos el periodo del mes pasado
    mes_actual = MESES[filters.month]
    if mes_actual == 1:
        mes_pasado = mes_actual
    else:
        mes_pasado = mes_actual - 1

    period_list = get_period_list(filters.year, filters.year, "Monthly")

    for p in period_list:
        if p['from_date'].month == mes_pasado:
            periodo = [p]

    asset = get_data(filters.company, "Asset", "Debit", periodo, only_current_fiscal_year=False)
    liability = get_data(filters.company, "Liability", "Credit", period_list, only_current_fiscal_year=False)
    equity = get_data(filters.company, "Equity", "Credit", period_list, only_current_fiscal_year=False)

    cuentas = asset + liability + equity

    # Falta Cheques
    totales_mes_anterior = {
        u'1003 - CAJA - U': 0,
        u'20 - Bco. Macro Cta. Cte. - U': 0,
        u'23 - Bco. Macro Licenciatura - U': 0,
        u'21 - Bco. Santa Fe Cta.Cte. - U': 0,
    }

    for cuenta in cuentas:
        if cuenta:
            if cuenta['account'] in totales_mes_anterior:
                totales_mes_anterior[cuenta['account']] = cuenta['total']

    accounts = frappe.db.sql("""
        select name
        from `tabAccount`
        where account_type ='Bank' or account_type = 'Cash'
        order by name asc
    """, as_dict=1)

    payment_entries = frappe.db.sql("""
        select `tabPayment Entry`.payment_type, `tabPayment Entry`.party_name, `tabPayment Entry`.posting_date,
               `tabPayment Entry`.paid_from, `tabPayment Entry`.paid_to, `tabPayment Entry`.paid_amount,
               `tabPayment Entry`.received_amount, `tabPayment Entry`.remarks
        from `tabPayment Entry`
        where MONTH(posting_date)=%s
        order by `tabPayment Entry`.posting_date
    """ % (MESES[filters.month]), as_dict=1)

    columns = get_columns(accounts)
    data = []

    for cuenta, total in totales_mes_anterior.iteritems():
        data.append({
            "cuenta": cuenta,
            "total": total,
        })

    for payment_entry in payment_entries:
        row = {
            'fecha': payment_entry.posting_date,
            'detalle': payment_entry.remarks,
            'party_name': payment_entry.party_name,
        }
        if payment_entry.payment_type == 'Pay':
            row[payment_entry.paid_from + 'E'] = '$ ' + str(payment_entry.paid_amount)
            data.append(row)

        elif payment_entry.payment_type == 'Receive':
            row[payment_entry.paid_to + 'I'] = '$ ' + str(payment_entry.received_amount)
            data.append(row)

    # Totales
    lista_totales = get_lista_totales(payment_entries, accounts)
    row = {'party_name': "Total", }
    for cuenta, total in lista_totales.iteritems():
        row[cuenta] = '$ ' + str(total)
    data.append(row)

    # Resultados del mes
    row = {'party_name': "Resultados del mes", }
    resultados_mes = get_resultados_mes(lista_totales, totales_mes_anterior)
    for cuenta, total in resultados_mes.iteritems():
        row[cuenta] = '$ ' + str(total)
    data.append(row)

    return columns, data


def get_resultados_mes(lista_totales, totales_mes_anterior):
    resultados = {}
    for cuenta, total in totales_mes_anterior.iteritems():
        if cuenta + 'I' in lista_totales:
            resultados[cuenta + 'I'] = total + lista_totales[cuenta + 'I'] - lista_totales[cuenta + 'E']
    return resultados


def get_lista_totales(payment_entries, accounts):
    totales = {}
    for payment in payment_entries:
        if payment.payment_type == 'Pay':
            if payment.paid_from + 'E' in totales:
                totales[payment.paid_from + 'E'] = totales[payment.paid_from + 'E'] + payment.paid_amount
            else:
                totales[payment.paid_from + 'E'] = payment.paid_amount
        elif payment.payment_type == 'Receive':
            if payment.paid_to + 'I' in totales:
                totales[payment.paid_to + 'I'] = totales[payment.paid_to + 'I'] + payment.received_amount
            else:
                totales[payment.paid_to + 'I'] = payment.received_amount

    for cuenta in accounts:
        nombre = cuenta["name"]
        if nombre + 'I' not in totales:
            totales[nombre + 'I'] = 0.0
        if nombre + 'E' not in totales:
            totales[nombre + 'E'] = 0.0
    return totales


def get_columns(accounts):
    columns = [
        {
            "fieldname": "cuenta",
            "label": "Cuenta",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "total",
            "label": "Total",
            "fieldtype": "Currency",
            "width": 90
        },
        {
            "fieldname": "fecha",
            "label": "Fecha",
            "fieldtype": "Date",
            "width": 90
        },
        {
            "fieldname": "detalle",
            "label": "Detalle",
            "fieldtype": "Data",
            "width": 90
        },
        {
            "fieldname": "party_name",
            "label": "Tercero",
            "fieldtype": "Data",
            "width": 180
        },
    ]

    for account in accounts:
        columns.append({
            "fieldname": account["name"] + 'I',
            "label": account["name"] + ' Ingresos',
            "fieldtype": "Data",
            "width": 150
        })
        columns.append({
            "fieldname": account["name"] + 'E',
            "label": account["name"] + ' Egresos',
            "fieldtype": "Data",
            "width": 150
        })
    return columns
