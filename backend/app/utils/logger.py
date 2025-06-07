import logging

def get_logger(name):
    """
    Retorna um logger configurado
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        
    Returns:
        Logger configurado ou NullLogger em caso de falha
    """
    try:
        logger = logging.getLogger(name)
        return logger
    except Exception:
        class NullLogger:
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
            def debug(self, *args, **kwargs): pass
        return NullLogger()
