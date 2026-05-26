const collector = (() => {
    let dwell           = []
    let flight          = []
    let keydownLog      = {}
    let lastKeyup       = null
    let backspaceCount  = 0
    let pasteDetected   = false
    let active          = false

    const IGNORED_KEYS = [
        'Shift', 'CapsLock', 'Tab', 'Alt', 'Control',
        'Meta', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'
    ]

    function attach(inputElement) {
        // Reset setiap kali field difokus
        inputElement.addEventListener('focus', () => {
            reset()
            active = true
        })

        inputElement.addEventListener('blur', () => {
            active = false
        })

        // Deteksi paste
        inputElement.addEventListener('paste', () => {
            pasteDetected = true
        })

        inputElement.addEventListener('keydown', (e) => {
            if (!active) return
            if (IGNORED_KEYS.includes(e.key)) return
            if (e.repeat) return

            // Hitung flight dari keyup sebelumnya
            if (lastKeyup !== null) {
                flight.push(
                    parseFloat((e.timeStamp - lastKeyup).toFixed(2))
                )
            }

            // Catat waktu keydown
            keydownLog[e.key] = e.timeStamp

            // Hitung backspace
            if (e.key === 'Backspace') {
                backspaceCount++
            }
        })

        inputElement.addEventListener('keyup', (e) => {
            if (!active) return
            if (IGNORED_KEYS.includes(e.key)) return

            const downTime = keydownLog[e.key]
            if (downTime === undefined) return

            // Hitung dwell — kecuali backspace
            if (e.key !== 'Backspace') {
                dwell.push(
                    parseFloat((e.timeStamp - downTime).toFixed(2))
                )
            }

            lastKeyup = e.timeStamp
            delete keydownLog[e.key]
        })
    }

    function collect() {
        return {
            dwell:  [...dwell],
            flight: [...flight],
            meta: {
                backspace_count: backspaceCount,
                paste_detected:  pasteDetected
            }
        }
    }

    function reset() {
        dwell          = []
        flight         = []
        keydownLog     = {}
        lastKeyup      = null
        backspaceCount = 0
        pasteDetected  = false
    }

    function init() {
        // Otomatis attach ke password field saat halaman load
        const passwordField = document.getElementById('password')
        if (passwordField) {
            attach(passwordField)
        }
    }

    // Jalankan saat DOM siap
    document.addEventListener('DOMContentLoaded', init)

    return { collect, reset }
})()