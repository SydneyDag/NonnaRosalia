document.addEventListener('DOMContentLoaded', function() {
    // Create alert container at the start
    const container = document.querySelector('.container');
    const alertContainer = document.createElement('div');
    alertContainer.className = 'alert-container mb-3';
    container.insertBefore(alertContainer, container.firstChild);

    const deliveryDate = document.getElementById('deliveryDate');
    const dailyDriverExpense = document.getElementById('dailyDriverExpense');
    const addOrderBtn = document.getElementById('addOrderBtn');
    
    // Initialize date picker with today's date
    deliveryDate.valueAsDate = new Date();

    function showError(message) {
        try {
            console.error(message);
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger alert-dismissible fade show';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Clear existing alerts
            while (alertContainer.firstChild) {
                alertContainer.removeChild(alertContainer.firstChild);
            }
            
            alertContainer.appendChild(alertDiv);
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode === alertContainer) {
                    alertDiv.remove();
                }
            }, 5000);
        } catch (error) {
            console.error('Error showing alert:', error);
        }
    }

    function showSuccess(message) {
        try {
            console.log(message);
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Clear existing alerts
            while (alertContainer.firstChild) {
                alertContainer.removeChild(alertContainer.firstChild);
            }
            
            alertContainer.appendChild(alertDiv);
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode === alertContainer) {
                    alertDiv.remove();
                }
            }, 3000);
        } catch (error) {
            console.error('Error showing alert:', error);
        }
    }

    const ordersTable = $('#ordersTable').DataTable({
        columns: [
            { data: 'customer_name' },
            { 
                data: 'total_cases',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm cases-input" 
                               value="${data || 0}" min="0" style="width: 80px">`;
                    }
                    return data || 0;
                }
            },
            { 
                data: 'total_cost',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm cost-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_cash',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input cash-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_check',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input check-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            { 
                data: 'payment_credit',
                render: function(data, type, row) {
                    if (type === 'display' && row.isEditable) {
                        return `<input type="number" class="form-control form-control-sm payment-input credit-input" 
                               value="${parseFloat(data || 0).toFixed(2)}" min="0" step="0.01" style="width: 100px">`;
                    }
                    return `$${parseFloat(data || 0).toFixed(2)}`;
                }
            },
            {
                data: 'payment_received',
                render: value => `$${parseFloat(value || 0).toFixed(2)}`
            }
        ],
        language: {
            emptyTable: "No orders found for the selected date",
            loadingRecords: "Loading orders...",
            zeroRecords: "No matching orders found",
            error: "Error loading order data"
        },
        footerCallback: function(row, data, start, end, display) {
            try {
                const api = this.api();
                // Calculate column totals
                const totals = {
                    cases: api.column(1, {page: 'current'}).data().reduce((a, b) => a + (parseInt(b) || 0), 0),
                    cost: api.column(2, {page: 'current'}).data().reduce((a, b) => {
                        const val = typeof b === 'string' ? b.replace('$', '') : b;
                        return a + (parseFloat(val) || 0);
                    }, 0),
                    cash: api.column(3, {page: 'current'}).data().reduce((a, b) => {
                        const val = typeof b === 'string' ? b.replace('$', '') : b;
                        return a + (parseFloat(val) || 0);
                    }, 0),
                    check: api.column(4, {page: 'current'}).data().reduce((a, b) => {
                        const val = typeof b === 'string' ? b.replace('$', '') : b;
                        return a + (parseFloat(val) || 0);
                    }, 0),
                    credit: api.column(5, {page: 'current'}).data().reduce((a, b) => {
                        const val = typeof b === 'string' ? b.replace('$', '') : b;
                        return a + (parseFloat(val) || 0);
                    }, 0),
                    payments: api.column(6, {page: 'current'}).data().reduce((a, b) => {
                        const val = typeof b === 'string' ? b.replace('$', '') : b;
                        return a + (parseFloat(val) || 0);
                    }, 0)
                };

                // Update summary elements
                const updateElement = (id, value, isMonetary = true) => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = isMonetary ? 
                            `$${parseFloat(value || 0).toFixed(2)}` : 
                            (parseInt(value || 0)).toString();
                    }
                };

                updateElement('totalCases', totals.cases, false);
                updateElement('totalCost', totals.cost);
                updateElement('totalPayments', totals.payments);
                updateElement('tableTotalCases', totals.cases, false);
                updateElement('tableTotalCost', totals.cost);
                updateElement('totalCashPayments', totals.cash);
                updateElement('totalCheckPayments', totals.check);
                updateElement('totalCreditPayments', totals.credit);
                updateElement('tableTotalPayments', totals.payments);
            } catch (error) {
                console.error('Error calculating totals:', error);
            }
        }
    });

    async function loadOrders() {
        try {
            if (!deliveryDate.value) {
                throw new Error('Please select a valid date');
            }

            const response = await fetch(`/api/orders/${deliveryDate.value}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to load orders');
            }

            const data = await response.json();
            if (!Array.isArray(data)) {
                throw new Error('Invalid response format');
            }

            const today = new Date().toISOString().split('T')[0];
            const processedData = data.map(order => ({
                ...order,
                isEditable: deliveryDate.value === today
            }));

            ordersTable.clear().rows.add(processedData).draw();
            return processedData;
        } catch (error) {
            console.error('Error loading orders:', error);
            showError('Failed to load orders: ' + error.message);
            ordersTable.clear().draw();
            return [];
        }
    }

    async function loadDailyDriverExpense() {
        try {
            if (!deliveryDate.value) {
                throw new Error('Please select a valid date');
            }

            const response = await fetch(`/api/daily_driver_expense/${deliveryDate.value}`);
            if (!response.ok && response.status !== 404) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to load driver expense');
            }

            if (response.status === 404) {
                dailyDriverExpense.value = '0';
                return;
            }

            const data = await response.json();
            if (!data || typeof data.amount !== 'number') {
                throw new Error('Invalid response format');
            }

            dailyDriverExpense.value = data.amount.toString();
        } catch (error) {
            console.error('Error loading driver expense:', error);
            dailyDriverExpense.value = '0';
            showError('Failed to load driver expense: ' + error.message);
        }
    }

    async function updateOrder(orderId, updatedData) {
        try {
            if (!orderId) throw new Error('Order ID is required');
            
            const response = await fetch(`/api/orders/${orderId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to update order');
            }

            await loadOrders();
            showSuccess('Order updated successfully');
        } catch (error) {
            console.error('Error updating order:', error);
            showError('Failed to update order: ' + error.message);
            throw error;
        }
    }

    async function saveDailyDriverExpense() {
        try {
            const amount = parseFloat(dailyDriverExpense.value);
            if (isNaN(amount) || amount < 0) {
                throw new Error('Please enter a valid expense amount');
            }

            const response = await fetch('/api/daily_driver_expense', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: deliveryDate.value,
                    amount: amount
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save driver expense');
            }

            await loadOrders();
            showSuccess('Driver expense saved successfully');
        } catch (error) {
            console.error('Error saving driver expense:', error);
            showError('Failed to save driver expense: ' + error.message);
        }
    }

    function collectRowData(row, originalData) {
        try {
            if (!row || !originalData) {
                throw new Error('Invalid row data');
            }

            const getValue = (selector) => {
                const input = row.find(selector);
                return input.length ? parseFloat(input.val()) || 0 : 0;
            };

            const data = {
                id: originalData.id,
                total_cases: getValue('.cases-input'),
                total_cost: getValue('.cost-input'),
                payment_cash: getValue('.cash-input'),
                payment_check: getValue('.check-input'),
                payment_credit: getValue('.credit-input')
            };

            if (data.total_cost < 0) throw new Error('Total cost cannot be negative');
            if (data.total_cases < 0) throw new Error('Cases cannot be negative');
            if (data.payment_cash < 0 || data.payment_check < 0 || data.payment_credit < 0) {
                throw new Error('Payments cannot be negative');
            }

            return data;
        } catch (error) {
            console.error('Error collecting row data:', error);
            throw error;
        }
    }

    function updateAddOrderButton() {
        const today = new Date().toISOString().split('T')[0];
        if (addOrderBtn) {
            addOrderBtn.style.display = deliveryDate.value === today ? 'block' : 'none';
        }
    }

    // Event Listeners
    deliveryDate.addEventListener('change', async () => {
        try {
            await Promise.all([loadOrders(), loadDailyDriverExpense()]);
            updateAddOrderButton();
        } catch (error) {
            console.error('Error updating data:', error);
            showError('Failed to update data: ' + error.message);
        }
    });

    document.getElementById('saveDriverExpense').addEventListener('click', saveDailyDriverExpense);

    $('#ordersTable').on('change', 'input', async function() {
        try {
            const row = $(this).closest('tr');
            const data = ordersTable.row(row).data();
            if (!data) {
                throw new Error('Could not find order data');
            }
            const updatedData = collectRowData(row, data);
            await updateOrder(data.id, updatedData);
        } catch (error) {
            console.error('Error updating order:', error);
            showError(error.message);
        }
    });

    // Initialize application
    Promise.all([
        loadOrders(),
        loadDailyDriverExpense()
    ]).then(() => {
        updateAddOrderButton();
    }).catch(error => {
        console.error('Error during initialization:', error);
        showError('Failed to initialize application: ' + error.message);
    });
});
