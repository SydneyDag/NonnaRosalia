document.addEventListener('DOMContentLoaded', function() {
    const customersTable = $('#customersTable').DataTable({
        dom: '<"row mb-3"<"col-md-6"B><"col-md-6"f>>rt<"row"<"col-md-6"l><"col-md-6"p>>',
        buttons: [
            {
                text: 'Reset Filters',
                className: 'btn btn-secondary',
                action: function () {
                    $('#territoryFilter').val('');
                    $('#deliveryDayFilter').val('');
                    $('#accountTypeFilter').val('');
                    customersTable.search('').columns().search('').draw();
                }
            }
        ],
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

    // Add filter controls above the table
    $('.card-body').prepend(`
        <div class="row mb-3">
            <div class="col-md-4">
                <select id="territoryFilter" class="form-select">
                    <option value="">All Territories</option>
                </select>
            </div>
            <div class="col-md-4">
                <select id="deliveryDayFilter" class="form-select">
                    <option value="">All Delivery Days</option>
                    <option value="Monday">Monday</option>
                    <option value="Tuesday">Tuesday</option>
                    <option value="Wednesday">Wednesday</option>
                    <option value="Thursday">Thursday</option>
                    <option value="Friday">Friday</option>
                </select>
            </div>
            <div class="col-md-4">
                <select id="accountTypeFilter" class="form-select">
                    <option value="">All Account Types</option>
                    <option value="Regular">Regular</option>
                    <option value="Corporate">Corporate</option>
                </select>
            </div>
        </div>
    `);

    // Load territories for the filter
    fetch('/api/territories')
        .then(response => response.json())
        .then(territories => {
            const territoryFilter = document.getElementById('territoryFilter');
            territoryFilter.innerHTML += territories.map(t => 
                `<option value="${t}">${t}</option>`
            ).join('');
        });

    // Add filter event listeners
    $('#territoryFilter').on('change', function() {
        customersTable.column(4).search(this.value).draw();
    });

    $('#deliveryDayFilter').on('change', function() {
        customersTable.column(2).search(this.value).draw();
    });

    $('#accountTypeFilter').on('change', function() {
        customersTable.column(3).search(this.value).draw();
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
