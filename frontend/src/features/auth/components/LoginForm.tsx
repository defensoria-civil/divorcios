import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../hooks/useAuth';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/Card';

const loginSchema = z.object({
  username: z.string().min(1, 'Usuario requerido'),
  password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login, isLoggingIn, loginError } = useAuth();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginFormData) => {
    login(data);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Card className="w-full max-w-md bg-slate-800 border-slate-700">
        <CardHeader className="space-y-1">
          <CardTitle className="text-center text-3xl text-white">⚖️ Defensoría Civil</CardTitle>
          <CardDescription className="text-center text-slate-300">
            Sistema de Asistencia Legal Automatizada
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none text-slate-200 peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Usuario
              </label>
              <Input
                type="text"
                placeholder="semper"
                {...register('username')}
                error={errors.username?.message}
                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium leading-none text-slate-200 peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Contraseña
              </label>
              <Input
                type="password"
                placeholder="••••••••"
                {...register('password')}
                error={errors.password?.message}
                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>

            {loginError && (
              <div className="rounded-md bg-red-900/20 border border-red-800 p-3 text-sm text-red-400">
                Error al iniciar sesión. Verifica tus credenciales.
              </div>
            )}

            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" isLoading={isLoggingIn}>
              Iniciar Sesión
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
