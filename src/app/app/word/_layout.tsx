import { Stack } from 'expo-router';
import { TouchableOpacity,StyleSheet, View} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function WordLayout() {
  return (
    <Stack>
      <Stack.Screen
        name='[name]'
        options={({ navigation }) => ({
          headerShown: true,
          headerLeft: () => (
            <View style={{marginRight:20}}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name='arrow-back' size={24} color='black' />
            </TouchableOpacity>
            </View>
          ),
        })}
      />
    </Stack>
  );
}

const styles = StyleSheet.create({
})