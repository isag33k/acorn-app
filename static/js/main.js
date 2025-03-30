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
    
    // Fix for dropdown menu z-index issues
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        userDropdown.addEventListener('click', function() {
            // When dropdown is clicked, make sure it appears in front
            setTimeout(function() {
                const dropdownMenu = document.querySelector('.dropdown-menu-end');
                if (dropdownMenu) {
                    // Get the position of the user dropdown button
                    const rect = userDropdown.getBoundingClientRect();
                    
                    // Calculate the right position (align with the right edge of the dropdown toggle)
                    const rightPosition = window.innerWidth - rect.right;
                    
                    // Apply the highest z-index and correct positioning
                    dropdownMenu.style.zIndex = "9999";
                    dropdownMenu.style.position = "fixed";
                    dropdownMenu.style.top = rect.bottom + 'px';
                    dropdownMenu.style.right = rightPosition + 'px';
                    dropdownMenu.style.left = 'auto';
                    
                    // Force browser to redraw the element
                    dropdownMenu.style.display = 'none';
                    void dropdownMenu.offsetHeight;
                    dropdownMenu.style.display = 'block';
                    
                    // Set card z-indices lower
                    document.querySelectorAll('.card, .container, main, .table-responsive').forEach(function(element) {
                        element.style.zIndex = "1";
                    });
                }
            }, 10);
        });
    }
    
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
    
    // Check for stuck modals every second
    let modalCheckInterval;
    function checkForStuckModals() {
        const modalResetHelper = document.getElementById('modalResetHelper');
        if (!modalResetHelper) return; // Skip if the element doesn't exist on this page
        
        if (document.body.classList.contains('modal-open')) {
            // If a modal has been open for more than 3 seconds, show the emergency button
            modalResetHelper.style.display = 'block';
        } else {
            // If no modal is open, hide the emergency button
            modalResetHelper.style.display = 'none';
        }
    }
    
    // Start checking for stuck modals
    modalCheckInterval = setInterval(checkForStuckModals, 1000);
    
    // Emergency modal reset button functionality
    const emergencyResetBtn = document.getElementById('emergencyModalReset');
    if (emergencyResetBtn) {
        emergencyResetBtn.addEventListener('click', function() {
            console.log("Emergency modal reset triggered");
            
            // Remove all modal-related classes and elements
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            // Remove all modal backdrops
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(function(backdrop) {
                backdrop.remove();
            });
            
            // Close all open modals by removing their show class
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                modal.classList.remove('show');
                modal.style.display = 'none';
                modal.setAttribute('aria-hidden', 'true');
            });
            
            // Hide the reset helper after use
            const resetHelper = document.getElementById('modalResetHelper');
            if (resetHelper) {
                resetHelper.style.display = 'none';
            }
            
            // Show a success message
            alert("Screen has been reset. You can continue using the application.");
        });
    }
    
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
    
    // Fix for modal backdrop issues
    // Handle proper closing of modals that might have backdrop issues
    const editModalElements = document.querySelectorAll('.modal');
    
    editModalElements.forEach(modal => {
        // Add event listener for when the modal is hidden
        modal.addEventListener('hidden.bs.modal', function() {
            // Ensure backdrop is removed
            document.body.classList.remove('modal-open');
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                backdrop.remove();
            });
            
            // Reset body styling that might have been added by Bootstrap
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
        
        // Add event listener for when the modal is shown
        modal.addEventListener('shown.bs.modal', function() {
            console.log('Modal shown:', modal.id);
        });
        
        // Add event listener for any form submissions inside modals
        const modalForms = modal.querySelectorAll('form');
        modalForms.forEach(form => {
            form.addEventListener('submit', function() {
                // Force close the modal properly before form submission
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        });
        
        // Add event listener for cancel/close buttons in modals
        const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Ensure the modal is fully closed
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
                
                // Manual cleanup
                document.body.classList.remove('modal-open');
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => {
                    backdrop.remove();
                });
                
                // Reset body styling
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            });
        });
    });
});
