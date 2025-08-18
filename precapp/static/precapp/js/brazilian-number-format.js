/**
 * Brazilian Number Formatting for Forms
 * Handles conversion between Brazilian format (15.000,50) and standard format (15000.50)
 */

// Format number to Brazilian format
function formatBrazilianNumber(value) {
    if (!value || value === '') return '';
    
    // Clean the input by removing all formatting
    let cleanValue = value.toString().replace(/\./g, '').replace(',', '.');
    let num = parseFloat(cleanValue);
    
    if (isNaN(num)) return '';
    
    // Only add decimals if the original value had them or if it's a currency field
    let hasDecimals = cleanValue.includes('.') || cleanValue.includes(',');
    
    if (hasDecimals) {
        return num.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    } else {
        // For whole numbers, check if user typed a decimal separator
        if (value.toString().includes(',') || value.toString().includes('.')) {
            return num.toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        } else {
            // Just format as integer with thousand separators
            return num.toLocaleString('pt-BR', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            });
        }
    }
}

// Convert Brazilian format to standard format
function parseBrazilianNumber(value) {
    if (!value || value === '') return '';
    
    // Remove thousand separators and replace comma with dot
    return value.toString().replace(/\./g, '').replace(',', '.');
}

// Apply Brazilian formatting to input field
function applyBrazilianFormatting(input) {
    // Avoid applying multiple event listeners to the same input
    if (input.hasAttribute('data-brazilian-formatted')) {
        return;
    }
    input.setAttribute('data-brazilian-formatted', 'true');
    
    // Store original value to detect changes
    let originalValue = input.value;
    
    input.addEventListener('blur', function() {
        let value = this.value.trim();
        if (value && value !== originalValue) {
            let standardValue = parseBrazilianNumber(value);
            let formattedValue = formatBrazilianNumber(value); // Pass original to detect user intent
            
            // Only update if the formatted value is different and valid
            if (formattedValue && formattedValue !== value) {
                this.value = formattedValue;
            }
        }
        originalValue = this.value;
    });
    
    input.addEventListener('focus', function() {
        originalValue = this.value;
    });
    
    input.addEventListener('input', function() {
        // Allow user to type naturally, store what they're typing
        let value = this.value;
        
        // Only allow valid characters for Brazilian numbers
        let cleanValue = value.replace(/[^0-9,.]/g, '');
        
        // Allow only one decimal separator
        let parts = cleanValue.split(/[,.]/);
        if (parts.length > 2) {
            // Keep only the first decimal separator
            if (cleanValue.includes(',')) {
                cleanValue = parts[0] + ',' + parts.slice(1).join('');
            } else {
                cleanValue = parts[0] + '.' + parts.slice(1).join('');
            }
        }
        
        // Limit decimal places to 2
        if (cleanValue.includes(',')) {
            let [integer, decimal] = cleanValue.split(',');
            if (decimal && decimal.length > 2) {
                cleanValue = integer + ',' + decimal.substring(0, 2);
            }
        } else if (cleanValue.includes('.')) {
            let dotCount = (cleanValue.match(/\./g) || []).length;
            if (dotCount === 1) {
                let [integer, decimal] = cleanValue.split('.');
                if (decimal && decimal.length > 2) {
                    cleanValue = integer + '.' + decimal.substring(0, 2);
                }
            }
        }
        
        if (cleanValue !== value) {
            this.value = cleanValue;
        }
    });
}

// Function to apply Brazilian formatting to a container (for dynamic content)
function initializeBrazilianFormattingForContainer(container) {
    // Apply to all inputs with class 'brazilian-currency'
    container.querySelectorAll('.brazilian-currency').forEach(function(input) {
        applyBrazilianFormatting(input);
        
        // Format initial value if it exists and looks like a raw number
        if (input.value && input.value.trim()) {
            let value = input.value.trim();
            // Only format if it looks like an unformatted number (no commas or multiple dots)
            if (!value.includes(',') && (value.match(/\./g) || []).length <= 1) {
                let num = parseFloat(value);
                if (!isNaN(num)) {
                    // For currency fields, always show 2 decimal places
                    input.value = num.toLocaleString('pt-BR', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }
            }
        }
    });
    
    // Apply to all inputs with class 'brazilian-number'  
    container.querySelectorAll('.brazilian-number').forEach(function(input) {
        applyBrazilianFormatting(input);
        
        // Format initial value if it exists and looks like a raw number
        if (input.value && input.value.trim()) {
            let value = input.value.trim();
            // Only format if it looks like an unformatted number
            if (!value.includes(',') && (value.match(/\./g) || []).length <= 1) {
                let num = parseFloat(value);
                if (!isNaN(num)) {
                    // For regular numbers, preserve decimal places as intended
                    let hasDecimals = value.includes('.') && value.split('.')[1];
                    if (hasDecimals) {
                        input.value = num.toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });
                    } else {
                        input.value = num.toLocaleString('pt-BR', {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 2
                        });
                    }
                }
            }
        }
    });
}

// Global function to apply Brazilian formatting to the entire document
function initializeBrazilianFormatting() {
    initializeBrazilianFormattingForContainer(document);
}

// Initialize Brazilian formatting on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeBrazilianFormatting();
    
    // Watch for Bootstrap collapse events to apply formatting to dropdown forms
    document.addEventListener('shown.bs.collapse', function(e) {
        // Apply formatting to the newly shown collapse element
        setTimeout(function() {
            initializeBrazilianFormattingForContainer(e.target);
        }, 50);
    });
    
    // Also watch for any other dynamic content that might be shown
    document.addEventListener('show.bs.collapse', function(e) {
        // Apply formatting when collapse is starting to show
        setTimeout(function() {
            initializeBrazilianFormattingForContainer(e.target);
        }, 100);
    });
    
    // Watch for modal events as well
    document.addEventListener('shown.bs.modal', function(e) {
        setTimeout(function() {
            initializeBrazilianFormattingForContainer(e.target);
        }, 50);
    });
    
    // Also handle dynamically added content with MutationObserver
    if (window.MutationObserver) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            // Check if the added node or its children have brazilian formatting classes
                            if (node.querySelectorAll && node.querySelectorAll('.brazilian-currency, .brazilian-number').length > 0) {
                                setTimeout(function() {
                                    initializeBrazilianFormattingForContainer(node);
                                }, 50);
                            }
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
});

// Convert Brazilian format back to standard format before form submission
document.addEventListener('submit', function(e) {
    // Find all Brazilian formatted inputs in the form being submitted
    e.target.querySelectorAll('.brazilian-currency, .brazilian-number').forEach(function(input) {
        if (input.value) {
            // Store the formatted value for display
            input.dataset.displayValue = input.value;
            // Convert to standard format for submission
            input.value = parseBrazilianNumber(input.value);
        }
    });
});
