/**
 * Brazilian Number Formatting for Forms
 * Handles conversion between Brazilian format (15.000,50) and standard format (15000.50)
 */

// Format number to Brazilian format
function formatBrazilianNumber(value) {
    if (!value || value === '') return '';
    
    // Convert to number and back to ensure proper formatting
    let num = parseFloat(value.toString().replace(/\./g, '').replace(',', '.'));
    if (isNaN(num)) return '';
    
    return num.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Convert Brazilian format to standard format
function parseBrazilianNumber(value) {
    if (!value || value === '') return '';
    
    // Remove thousand separators and replace comma with dot
    return value.toString().replace(/\./g, '').replace(',', '.');
}

// Apply Brazilian formatting to input field
function applyBrazilianFormatting(input) {
    input.addEventListener('blur', function() {
        let value = this.value;
        if (value) {
            let standardValue = parseBrazilianNumber(value);
            let formattedValue = formatBrazilianNumber(standardValue);
            this.value = formattedValue;
        }
    });
    
    input.addEventListener('focus', function() {
        // Optional: remove formatting when focused for easier editing
        // Uncomment the lines below if you want this behavior
        // let value = this.value;
        // if (value) {
        //     this.value = parseBrazilianNumber(value);
        // }
    });
}

// Initialize Brazilian formatting on page load
document.addEventListener('DOMContentLoaded', function() {
    // Apply to all inputs with class 'brazilian-currency'
    document.querySelectorAll('.brazilian-currency').forEach(function(input) {
        applyBrazilianFormatting(input);
        
        // Format initial value if it exists
        if (input.value) {
            input.value = formatBrazilianNumber(input.value);
        }
    });
    
    // Apply to all inputs with class 'brazilian-number'
    document.querySelectorAll('.brazilian-number').forEach(function(input) {
        applyBrazilianFormatting(input);
        
        // Format initial value if it exists
        if (input.value) {
            input.value = formatBrazilianNumber(input.value);
        }
    });
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
