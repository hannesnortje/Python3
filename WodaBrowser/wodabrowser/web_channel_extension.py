
from PyQt6.QtCore import QObject, pyqtSignal, QJsonValue, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel, QWebChannelAbstractTransport

class EnhancedWebChannel(QWebChannel):
    """An enhanced web channel that better handles signal exposure to JavaScript."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._signal_handlers = {}
        self._debug_mode = True
        
    def registerObject(self, id, obj):
        """Register an object with enhanced signal support."""
        # Register the object with the channel
        super().registerObject(id, obj)
        
        # Save a reference to the object
        if not hasattr(self, "_registered_objects"):
            self._registered_objects = {}
        self._registered_objects[id] = obj
        
        # Process all signals on the object
        self._register_signals(id, obj)
        
    def _register_signals(self, id, obj):
        """Register all signals on an object for JavaScript exposure."""
        for attr_name in dir(obj):
            attr = getattr(obj, attr_name)
            if isinstance(attr, pyqtSignal):
                # Create a signal handler
                signal_handler = SignalHandler(obj, attr_name, id, self)
                
                # Store the handler to prevent garbage collection
                if id not in self._signal_handlers:
                    self._signal_handlers[id] = {}
                self._signal_handlers[id][attr_name] = signal_handler
                
                if self._debug_mode:
                    print(f"Registered signal: {id}.{attr_name}")

    def debug(self, enabled=True):
        """Enable or disable debug output."""
        self._debug_mode = enabled
        return self

class SignalHandler(QObject):
    """Handler that exposes PyQt signals as proper JavaScript signals."""
    
    # Signal that will be exposed to JavaScript
    signalFired = pyqtSignal(['QVariant'], ['QVariantList'], name='signalFired')
    
    def __init__(self, obj, signal_name, obj_id, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.signal_name = signal_name
        self.obj_id = obj_id
        
        # Connect the original signal to our handler
        signal = getattr(obj, signal_name)
        signal.connect(self._handle_signal)
        
        print(f"Signal handler created for: {obj_id}.{signal_name}")
    
    @pyqtSlot('QVariant')
    @pyqtSlot('QVariantList')
    def _handle_signal(self, *args):
        """Handle the signal and emit our JavaScript-friendly signal."""
        print(f"Signal {self.obj_id}.{self.signal_name} fired with args: {args}")
        if len(args) == 0:
            self.signalFired.emit(None)
        elif len(args) == 1:
            self.signalFired.emit(args[0])
        else:
            self.signalFired.emit(list(args))
