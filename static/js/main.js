/**
 * Main JavaScript for the Network Circuit Monitor application
 */

// Function to toggle credential fields in the Add Equipment form
function toggleCredentialFields() {
    const credentialType = document.getElementById('credential_type').value;
    const credentialFields = document.querySelectorAll('.credential-fields');
    
    if (credentialType === 'tacacs') {
        // Hide username/password fields
        credentialFields.forEach(field => {
            field.style.display = 'none';
        });
        
        // Set a hidden value for TACACS
        document.getElementById('username').value = 'TACACS';
        document.getElementById('password').value = 'TACACS_PLACEHOLDER';
    } else {
        // Show username/password fields
        credentialFields.forEach(field => {
            field.style.display = 'block';
        });
        
        // Clear the fields
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
    }
}

// Function to toggle credential fields in Edit Equipment form
function toggleEditCredentialFields(itemId) {
    const credentialType = document.getElementById(`edit_credential_type${itemId}`).value;
    const credentialFields = document.querySelectorAll(`.edit-credential-fields${itemId}`);
    
    if (credentialType === 'tacacs') {
        // Hide username/password fields
        credentialFields.forEach(field => {
            field.style.display = 'none';
        });
        
        // Set a hidden value for TACACS
        document.getElementById(`edit_username${itemId}`).value = 'TACACS';
        document.getElementById(`edit_password${itemId}`).value = '';
    } else {
        // Show username/password fields
        credentialFields.forEach(field => {
            field.style.display = 'block';
        });
        
        // Only clear if it was TACACS before
        if (document.getElementById(`edit_username${itemId}`).value === 'TACACS') {
            document.getElementById(`edit_username${itemId}`).value = '';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded - initializing tabs");
    
    // Initialize credential fields on page load
    const credentialTypeSelect = document.getElementById('credential_type');
    if (credentialTypeSelect) {
        toggleCredentialFields();
    }
    
    // Tab switching functionality
    document.querySelectorAll('.nav-tabs .nav-link').forEach(function(tabLink) {
        tabLink.addEventListener('click', function(e) {
            console.log("Tab clicked:", this.getAttribute('data-bs-target'));
            e.preventDefault();
            
            // Hide all tabs
            document.querySelectorAll('.tab-pane').forEach(function(tab) {
                tab.classList.remove('show', 'active');
            });
            
            // Show the selected tab
            const target = document.querySelector(this.getAttribute('data-bs-target'));
            target.classList.add('show', 'active');
            
            // Update active state on tab buttons
            document.querySelectorAll('.nav-tabs .nav-link').forEach(function(link) {
                link.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
    
    // Log that the tab initialization is complete
    console.log("Tab event listeners initialized");
    
    // Handle Tab Helper Buttons
    const showCircuitTabBtn = document.getElementById('showCircuitTab');
    if (showCircuitTabBtn) {
        showCircuitTabBtn.addEventListener('click', function() {
            // Find the circuit mappings tab and click it
            const circuitsTab = document.getElementById('circuits-tab');
            if (circuitsTab) {
                // Simulate a click on the circuits tab
                console.log("Showing circuit mappings tab via button");
                
                // Hide all tabs first
                document.querySelectorAll('.tab-pane').forEach(function(tab) {
                    tab.classList.remove('show', 'active');
                });
                
                // Show the circuits tab and set it as active
                const circuitsPane = document.getElementById('circuits');
                circuitsPane.classList.add('show', 'active');
                
                // Update active state on tab buttons
                document.querySelectorAll('.nav-tabs .nav-link').forEach(function(link) {
                    link.classList.remove('active');
                });
                circuitsTab.classList.add('active');
                
                // Highlight the edit buttons by adding a temporary class
                document.querySelectorAll('#circuits .btn-sm.btn-primary').forEach(function(btn) {
                    btn.classList.add('btn-lg');
                    setTimeout(function() {
                        btn.classList.remove('btn-lg');
                    }, 1500);
                });
            }
        });
    }
    
    // Add helper text for equipment edit
    const tabHelper = document.getElementById('tabHelper');
    if (tabHelper) {
        // Create equipment edit helper text
        const equipmentEditHelper = document.createElement('div');
        equipmentEditHelper.className = 'mt-2';
        equipmentEditHelper.innerHTML = `
            <p class="mb-0"><strong>NEW:</strong> You can now edit equipment details using the <span class="badge bg-primary"><i class="fas fa-edit"></i></span> button.</p>
            <button class="btn btn-sm btn-info mt-2" id="highlightEditButtons">Highlight Edit Buttons</button>
        `;
        
        // Add it to the helper panel
        tabHelper.appendChild(equipmentEditHelper);
        
        // Add event listener for the highlight button
        const highlightBtn = document.getElementById('highlightEditButtons');
        if (highlightBtn) {
            highlightBtn.addEventListener('click', function() {
                // Highlight all edit buttons
                document.querySelectorAll('.btn-sm.btn-primary').forEach(function(btn) {
                    btn.classList.add('btn-lg');
                    setTimeout(function() {
                        btn.classList.remove('btn-lg');
                    }, 1500);
                });
            });
        }
    }
    
    // Handle alert dismissal
    const alerts = document.querySelectorAll('.alert-dismissible');
    
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.btn-close');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                alert.classList.remove('show');
                
                setTimeout(() => {
                    alert.remove();
                }, 300);
            });
        }
    });
    
    // Auto-focus the circuit ID field on the index page
    const circuitIdField = document.getElementById('circuit_id');
    if (circuitIdField) {
        circuitIdField.focus();
    }
    
    // Add confirmation for delete operations
    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const confirmed = confirm('Are you sure you want to delete this item?');
            
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});
