class LifecycleService:
    """Application lifecycle logic outside the UI layer."""

    @staticmethod
    def confirm_shutdown(file_handler, settings_manager):
        """Close open files and persist settings when shutdown is confirmed."""
        if not file_handler.close_all_files():
            return False

        settings_manager.sync()
        return True
