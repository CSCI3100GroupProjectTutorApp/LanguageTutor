import { Stack } from 'expo-router';
import { TouchableOpacity,StyleSheet, View} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function translateLayout() {
  return (
    <Stack>
      <Stack.Screen
        name='[text]'
        options={({ navigation }) => ({
          headerShown: true,
          headerLeft: () => (
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name='arrow-back' size={24} color='black' />
            </TouchableOpacity>
          ),
        })}
      />
    </Stack>
  );
}

const styles = StyleSheet.create({
})