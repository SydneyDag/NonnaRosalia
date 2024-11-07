document.addEventListener('DOMContentLoaded', function() {
    const customersTable = $('#customersTable').DataTable({
        columns: [
            { data: 'name' },
            { data: 'address' },
            { data: 'delivery_day' },
            { data: 'account_type' },
            { data: 'territory' },
            { 
                data: 'balance',
                render: value => `$${parseFloat(value).toFixed(2)}`
            },
            {
                data: 'id',
                render: function(data) {
                    return `
                        <button class="btn btn-sm btn-primary edit-customer" data-id="${data}">Edit</button>
                        <button class="btn btn-sm btn-danger delete-customer" data-id="${data}">Delete</button>
                    `;
                }
            }
        ]
    });

    loadCustomers();

    document.getElementById('saveCustomer').addEventListener('click', saveCustomer);
    
    $('#customersTable').on('click', '.edit-customer', function() {
        const id = $(this).data('id');
        const row = customersTable.row($(this).parents('tr')).data();
        populateForm(row);
        $('#customerModal').modal('show');
    });

    $('#customersTable').on('click', '.delete-customer', function() {
        if (confirm('Are you sure you want to delete this customer?')) {
            const id = $(this).data('id');
            deleteCustomer(id);
        }
    });

    function loadCustomers() {
        fetch('/api/customers')
            .then(response => response.json())
            .then(data => {
                customersTable.clear().rows.add(data).draw();
            });
    }

    function populateForm(data) {
        document.getElementById('customerId').value = data.id;
        document.getElementById('name').value = data.name;
        document.getElementById('address').value = data.address;
        document.getElementById('deliveryDay').value = data.delivery_day;
        document.getElementById('accountType').value = data.account_type;
        document.getElementById('territory').value = data.territory;
    }

    function saveCustomer() {
        const id = document.getElementById('customerId').value;
        const data = {
            name: document.getElementById('name').value,
            address: document.getElementById('address').value,
            delivery_day: document.getElementById('deliveryDay').value,
            account_type: document.getElementById('accountType').value,
            territory: document.getElementById('territory').value
        };

        const method = id ? 'PUT' : 'POST';
        if (id) data.id = id;

        fetch('/customers', {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(() => {
            $('#customerModal').modal('hide');
            loadCustomers();
        });
    }

    function deleteCustomer(id) {
        fetch('/customers', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        })
        .then(response => response.json())
        .then(() => {
            loadCustomers();
        });
    }
});
