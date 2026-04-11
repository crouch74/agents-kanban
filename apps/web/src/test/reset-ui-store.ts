import { useUIStore } from '@/store/ui';

export function resetUIStore() {
  useUIStore.setState({
    selectedProjectId: null,
    inspectorOpen: true,
  });
}
