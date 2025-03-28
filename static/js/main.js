/**
 * Main JavaScript for the Network Circuit Monitor application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tabs
    var triggerTabList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tab"]'))
    triggerTabList.forEach(function(triggerEl) {
        new bootstrap.Tab(triggerEl);
    });
    
    // Manually handle tab link clicks if needed
    const tabLinks = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabLinks.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get target tab
            const target = document.querySelector(this.getAttribute('data-bs-target'));
            
            // Remove active class from all tabs and panes
            document.querySelectorAll('.nav-link').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => {
                p.classList.remove('show');
                p.classList.remove('active');
            });
            
            // Add active class to current tab and pane
            this.classList.add('active');
            target.classList.add('show');
            target.classList.add('active');
        });
    });
    
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
