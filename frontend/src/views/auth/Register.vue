<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/theme';
import { Sun, Moon } from 'lucide-vue-next';
import Input from '@/components/ui/Input.vue';
import Button from '@/components/ui/Button.vue';
import * as z from 'zod';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';

const router = useRouter();
const authStore = useAuthStore();
const themeStore = useThemeStore();
const errorMsg = ref('');

const registerSchema = toTypedSchema(
  z.object({
    name: z.string().min(1, 'Name is required'),
    email: z.string().min(1, 'Email is required').email('Invalid email format'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
  })
);

const { handleSubmit, errors, defineField, isSubmitting } = useForm({
  validationSchema: registerSchema,
});

const [name, nameProps] = defineField('name');
const [email, emailProps] = defineField('email');
const [password, passwordProps] = defineField('password');

const onSubmit = handleSubmit(async (values) => {
  errorMsg.value = '';
  try {
    await authStore.register(values);
    router.push('/login');
  } catch (err) {
    errorMsg.value = err.response?.data?.message || err.message || 'Registration failed';
  }
});
</script>

<template>
  <div class="relative">
    <button @click="themeStore.toggleDark()"
      class="absolute top-4 right-4 p-2 rounded-full hover:bg-secondary transition-colors text-muted-foreground">
      <Moon v-if="!themeStore.isDark" class="w-5 h-5" />
      <Sun v-else class="w-5 h-5 text-yellow-500" />
    </button>

    <div class="p-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold tracking-tight text-foreground">Create an account</h1>
        <p class="text-sm text-muted-foreground mt-2">Enter your details below to create your account</p>
      </div>

      <form @submit="onSubmit" class="space-y-6">
        <div v-if="errorMsg" class="p-3 text-sm bg-rose-500/10 text-rose-500 border border-rose-500/20 rounded-lg">
          {{ errorMsg }}
        </div>

        <Input 
          id="name" 
          v-model="name" 
          v-bind="nameProps"
          type="text" 
          label="Full Name" 
          placeholder="John Doe" 
          :error="errors.name"
        />

        <Input 
          id="email" 
          v-model="email" 
          v-bind="emailProps"
          type="email" 
          label="Email" 
          placeholder="m@example.com" 
          :error="errors.email"
        />

        <Input 
          id="password" 
          v-model="password" 
          v-bind="passwordProps"
          type="password" 
          label="Password" 
          placeholder="Minimum 6 characters" 
          :error="errors.password"
        />

        <Button type="submit" :loading="isSubmitting || authStore.loading" customClass="w-full text-md">
          Create Account
        </Button>
      </form>

      <div class="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?
        <router-link to="/login" class="font-medium text-primary hover:underline">Sign in</router-link>
      </div>
    </div>
  </div>
</template>
