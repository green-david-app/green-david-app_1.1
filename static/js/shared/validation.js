// ============================================
// FORM VALIDATION MODULE
// ============================================

/**
 * Validation rules
 */
const ValidationRules = {
    required: (value) => {
        if (!value || (typeof value === 'string' && !value.trim())) {
            return 'Toto pole je povinné';
        }
        return null;
    },
    
    minLength: (min) => (value) => {
        if (value && value.length < min) {
            return `Minimálně ${min} znaků`;
        }
        return null;
    },
    
    maxLength: (max) => (value) => {
        if (value && value.length > max) {
            return `Maximálně ${max} znaků`;
        }
        return null;
    },
    
    email: (value) => {
        if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            return 'Neplatný email';
        }
        return null;
    },
    
    phone: (value) => {
        if (value && !/^[\d\s\+\-\(\)]+$/.test(value)) {
            return 'Neplatné telefonní číslo';
        }
        return null;
    },
    
    date: (value) => {
        if (value && isNaN(Date.parse(value))) {
            return 'Neplatné datum';
        }
        return null;
    },
    
    dateRange: (startDate, endDate) => {
        if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
            return 'Datum začátku musí být před datem konce';
        }
        return null;
    },
    
    number: (value) => {
        if (value && isNaN(Number(value))) {
            return 'Musí být číslo';
        }
        return null;
    },
    
    min: (min) => (value) => {
        if (value && Number(value) < min) {
            return `Minimální hodnota je ${min}`;
        }
        return null;
    },
    
    max: (max) => (value) => {
        if (value && Number(value) > max) {
            return `Maximální hodnota je ${max}`;
        }
        return null;
    }
};

/**
 * Validate single field
 */
function validateField(value, rules) {
    if (!Array.isArray(rules)) {
        rules = [rules];
    }
    
    for (const rule of rules) {
        const error = typeof rule === 'function' ? rule(value) : null;
        if (error) return error;
    }
    return null;
}

/**
 * Validate entire form
 */
function validateForm(formData, schema) {
    const errors = {};
    
    for (const [field, rules] of Object.entries(schema)) {
        const value = formData[field];
        const error = validateField(value, rules);
        if (error) {
            errors[field] = error;
        }
    }
    
    return {
        isValid: Object.keys(errors).length === 0,
        errors
    };
}

/**
 * Show validation errors in UI
 */
function showValidationErrors(errors) {
    // Clear previous errors
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll('.input-error').forEach(el => {
        el.classList.remove('input-error');
    });
    
    // Show new errors
    for (const [field, message] of Object.entries(errors)) {
        const input = document.getElementById(field) || 
                     document.querySelector(`[name="${field}"]`);
        
        if (input) {
            // Add error class to input
            input.classList.add('input-error');
            
            // Add error message
            const errorEl = document.createElement('div');
            errorEl.className = 'field-error';
            errorEl.textContent = message;
            
            // Insert after input or in parent
            const parent = input.parentElement;
            if (parent) {
                parent.appendChild(errorEl);
            } else {
                input.insertAdjacentElement('afterend', errorEl);
            }
            
            // Focus first error
            if (!document.querySelector('.input-error:focus')) {
                input.focus();
            }
        }
    }
}

/**
 * Validate job form
 */
function validateJobForm(formData) {
    const schema = {
        title: [
            ValidationRules.required,
            ValidationRules.minLength(3),
            ValidationRules.maxLength(100)
        ],
        client: [
            ValidationRules.maxLength(100)
        ],
        address: [
            ValidationRules.maxLength(200)
        ],
        created_date: [
            ValidationRules.date
        ],
        start_date: [
            ValidationRules.date
        ],
        deadline: [
            ValidationRules.date
        ],
        progress: [
            ValidationRules.number,
            ValidationRules.min(0),
            ValidationRules.max(100)
        ]
    };
    
    const result = validateForm(formData, schema);
    
    // Additional custom validation
    if (formData.start_date && formData.created_date) {
        const error = ValidationRules.dateRange(
            formData.created_date, 
            formData.start_date
        );
        if (error) {
            result.isValid = false;
            result.errors.start_date = 'Datum zahájení musí být po datu zadání';
        }
    }
    
    if (formData.deadline && formData.start_date) {
        const error = ValidationRules.dateRange(
            formData.start_date,
            formData.deadline
        );
        if (error) {
            result.isValid = false;
            result.errors.deadline = 'Deadline musí být po datu zahájení';
        }
    }
    
    return result;
}

// CSS pro error states
const errorStyles = `
.input-error {
    border-color: #ef4444 !important;
    background: rgba(248, 113, 113, 0.1) !important;
}

.field-error {
    color: #ef4444;
    font-size: 12px;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
}

.field-error::before {
    content: '⚠️';
    margin-right: 4px;
}
`;

// Inject styles
if (!document.getElementById('validation-styles')) {
    const style = document.createElement('style');
    style.id = 'validation-styles';
    style.textContent = errorStyles;
    document.head.appendChild(style);
}

// Export
window.Validation = {
    ValidationRules,
    validateField,
    validateForm,
    validateJobForm,
    showValidationErrors
};


