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

const loginSchema = toTypedSchema(
  z.object({
    email: z.string().min(1, 'Email is required').email('Invalid email format'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
  })
);

const { handleSubmit, errors, defineField, isSubmitting } = useForm({
  validationSchema: loginSchema,
});

const [email, emailProps] = defineField('email');
const [password, passwordProps] = defineField('password');

const onSubmit = handleSubmit(async (values) => {
  errorMsg.value = '';
  try {
    await authStore.login(values);
    router.push('/app/dashboard');
  } catch (error) {
    errorMsg.value = authStore.error || error.message || 'Login failed';
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
        <h1 class="text-2xl font-bold tracking-tight text-foreground">Welcome back</h1>
        <p class="text-sm text-muted-foreground mt-2">Enter your credentials to access your account</p>
      </div>

      <form @submit="onSubmit" class="space-y-6">
        <div v-if="errorMsg" class="p-3 text-sm bg-rose-500/10 text-rose-500 border border-rose-500/20 rounded-lg">
          {{ errorMsg }}
        </div>

        <Input 
          id="email" 
          v-model="email" 
          v-bind="emailProps"
          type="email" 
          label="Email" 
          placeholder="admin@kampus.ac.id"
          :error="errors.email"
        />

        <Input 
          id="password" 
          v-model="password" 
          v-bind="passwordProps"
          type="password" 
          label="Password" 
          placeholder="password"
          :error="errors.password"
        >
          <template #label-extra>
            <a href="#" class="text-sm text-primary hover:underline">Forgot password?</a>
          </template>
        </Input>

        <Button type="submit" :loading="isSubmitting || authStore.loading" customClass="w-full text-md">
          {{ isSubmitting || authStore.loading ? 'Signing in...' : 'Sign in' }}
        </Button>
      </form>

      <div class="mt-6 text-center text-sm text-muted-foreground">
        Don't have an account?
        <router-link to="/register" class="font-medium text-primary hover:underline">Sign up</router-link>
      </div>

    </div>
  </div>
</template>
